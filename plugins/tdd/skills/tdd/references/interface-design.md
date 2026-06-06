# Interface Design for Testability

The most important property of a testable interface:

**Accept dependencies, don't create them.**

```typescript
// Testable
function processOrder(order, paymentGateway) {}

// Hard to test
function processOrder(order) {
  const gateway = new StripeGateway();
}
```

When a dependency is hard-wired inside a function, you can't replace it with a test double at the boundary. Pass it in instead.
