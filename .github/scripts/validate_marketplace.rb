#!/usr/bin/env ruby
# frozen_string_literal: true

# Static validator for the Flagrant skills marketplace.
# Run from the repo root: `ruby .github/scripts/validate_marketplace.rb`
# Exits non-zero and prints a summary if any plugin or skill fails validation.

require "json"
require "pathname"

REPO_ROOT = Pathname.new(__dir__).parent.parent.expand_path
MARKETPLACE_MANIFEST = ".claude-plugin/marketplace.json"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
SKILL_FILENAME = "SKILL.md"
MIN_DESCRIPTION_LEN = 20
REQUIRED_SKILL_FIELDS = %w[name description].freeze
REQUIRED_PLUGIN_FIELDS = %w[name description version].freeze

def parse_frontmatter(text)
  unless text.start_with?("---\n")
    return [{}, "file does not start with '---' frontmatter fence"]
  end

  end_idx = text.index("\n---\n", 4)
  return [{}, "closing '---' frontmatter fence not found"] unless end_idx

  block = text[4...end_idx]
  data = {}
  current_key = nil

  block.each_line do |raw_line|
    line = raw_line.chomp
    next if line.strip.empty?

    if (match = line.match(/^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$/))
      current_key = match[1]
      data[current_key] = match[2].strip
    elsif current_key && line.match?(/^[ \t]/)
      data[current_key] = "#{data[current_key]} #{line.strip}".strip
    else
      return [{}, "unparseable frontmatter line: #{line.inspect}"]
    end
  end

  [data, nil]
end

def validate_skill(skill_dir)
  errors = []
  skill_file = skill_dir / SKILL_FILENAME
  unless skill_file.exist?
    errors << "missing #{SKILL_FILENAME}"
    return errors
  end

  data, parse_err = parse_frontmatter(skill_file.read)
  if parse_err
    errors << "#{SKILL_FILENAME}: #{parse_err}"
    return errors
  end

  REQUIRED_SKILL_FIELDS.each do |field|
    if data[field].nil? || data[field].empty?
      errors << "#{SKILL_FILENAME}: missing required field '#{field}'"
    end
  end

  name = data["name"].to_s
  if !name.empty? && name != skill_dir.basename.to_s
    errors << "#{SKILL_FILENAME}: name '#{name}' does not match directory '#{skill_dir.basename}'"
  end

  desc = data["description"].to_s
  unless desc.empty?
    if desc.length < MIN_DESCRIPTION_LEN
      errors << "#{SKILL_FILENAME}: description is too short " \
                "(#{desc.length} < #{MIN_DESCRIPTION_LEN} chars)"
    end
    first_char = desc[0]
    if first_char && first_char == first_char.downcase && first_char != first_char.upcase
      errors << "#{SKILL_FILENAME}: description should start with a capital letter"
    end
  end

  errors
end

def validate_plugin(plugin_dir)
  errors = []
  manifest_path = plugin_dir / PLUGIN_MANIFEST
  unless manifest_path.exist?
    errors << "missing #{PLUGIN_MANIFEST}"
    return { errors: errors, manifest: nil, skill_dirs: [] }
  end

  begin
    manifest = JSON.parse(manifest_path.read)
  rescue JSON::ParserError => e
    errors << "#{PLUGIN_MANIFEST}: JSON parse error: #{e.message}"
    return { errors: errors, manifest: nil, skill_dirs: [] }
  end

  REQUIRED_PLUGIN_FIELDS.each do |field|
    if manifest[field].nil? || manifest[field].to_s.empty?
      errors << "#{PLUGIN_MANIFEST}: missing required field '#{field}'"
    end
  end

  if manifest["name"] && manifest["name"] != plugin_dir.basename.to_s
    errors << "#{PLUGIN_MANIFEST}: name '#{manifest["name"]}' does not match plugin directory '#{plugin_dir.basename}'"
  end

  skills_root = plugin_dir / "skills"
  skill_dirs = []
  if skills_root.directory?
    skill_dirs = skills_root.children.sort.select(&:directory?)
    skill_dirs.each do |skill_dir|
      skill_errors = validate_skill(skill_dir)
      skill_errors.each { |err| errors << "skills/#{skill_dir.basename}/#{err}" }
    end
  end

  if skill_dirs.empty? && !(plugin_dir / "commands").directory? && !(plugin_dir / "agents").directory?
    errors << "plugin has no skills/, commands/, or agents/ directory — nothing to ship"
  end

  { errors: errors, manifest: manifest, skill_dirs: skill_dirs }
end

def validate_marketplace(root)
  manifest_path = root / MARKETPLACE_MANIFEST
  return [["root", ["missing #{MARKETPLACE_MANIFEST}"]], nil] unless manifest_path.exist?

  begin
    manifest = JSON.parse(manifest_path.read)
  rescue JSON::ParserError => e
    return [["root", ["#{MARKETPLACE_MANIFEST}: JSON parse error: #{e.message}"]], nil]
  end

  errors = []
  errors << "#{MARKETPLACE_MANIFEST}: missing 'name'" if manifest["name"].to_s.empty?
  errors << "#{MARKETPLACE_MANIFEST}: missing 'owner.name'" if manifest.dig("owner", "name").to_s.empty?

  plugins = manifest["plugins"]
  unless plugins.is_a?(Array) && !plugins.empty?
    errors << "#{MARKETPLACE_MANIFEST}: 'plugins' must be a non-empty array"
    return [["root", errors], manifest]
  end

  plugins.each_with_index do |entry, idx|
    prefix = "#{MARKETPLACE_MANIFEST}: plugins[#{idx}]"
    errors << "#{prefix}: missing 'name'" if entry["name"].to_s.empty?
    source = entry["source"].to_s
    if source.empty?
      errors << "#{prefix}: missing 'source'"
      next
    end
    unless source.start_with?("./")
      errors << "#{prefix}: source '#{source}' must be a relative path starting with './'"
    end
    resolved = (root / source).cleanpath
    unless resolved.directory?
      errors << "#{prefix}: source '#{source}' does not resolve to a directory"
    end
  end

  [["root", errors], manifest]
end

def main
  total_errors = 0

  (root_label, root_errors), marketplace_manifest = validate_marketplace(REPO_ROOT)
  status = root_errors.empty? ? "OK" : "FAIL"
  puts "[#{status}] marketplace (#{root_label})"
  root_errors.each { |err| puts "    - #{err}" }
  total_errors += root_errors.length

  plugin_dirs = []
  plugins_root = REPO_ROOT / "plugins"
  if plugins_root.directory?
    plugin_dirs = plugins_root.children.sort.select(&:directory?)
  end

  if plugin_dirs.empty?
    puts "[FAIL] plugins/"
    puts "    - no plugin directories found under plugins/"
    total_errors += 1
  end

  listed_names = (marketplace_manifest&.dig("plugins") || []).map { |p| p["name"] }
  plugin_dirs.each do |plugin_dir|
    result = validate_plugin(plugin_dir)
    unless listed_names.include?(plugin_dir.basename.to_s)
      result[:errors] << "plugin '#{plugin_dir.basename}' is not listed in #{MARKETPLACE_MANIFEST}"
    end

    status = result[:errors].empty? ? "OK" : "FAIL"
    puts "[#{status}] plugins/#{plugin_dir.basename}"
    result[:errors].each { |err| puts "    - #{err}" }
    total_errors += result[:errors].length
  end

  puts
  puts "#{plugin_dirs.length} plugin(s) checked, #{total_errors} error(s)"
  total_errors.zero? ? 0 : 1
end

exit(main) if __FILE__ == $PROGRAM_NAME
