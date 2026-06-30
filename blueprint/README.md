# QWireMock Refactoring Blueprint (Independent from Existing Code)

This directory plans a **Python-based** simulation platform including:
- Mock Order Processing Service (Order Service)
- Mock Initiator Callback Service (Callback Server)

> Constraint: this blueprint does not depend on, reference, or modify any existing implementation in this repository.

## Document Index
- `spec/order-service.spec.yaml`: order processing service specification
- `spec/callback-service.spec.yaml`: callback service specification
- `spec/shared-contracts.spec.yaml`: shared cross-module contracts and conventions
- `structure/target-directory-structure.md`: target project structure

## English Version Index
- `blueprint-guide.md`: Chinese master guide
- `PLAN.en.md`: English implementation plan
- `spec/order-service.spec.en.yaml`: order service spec
- `spec/callback-service.spec.en.yaml`: callback service spec
- `spec/shared-contracts.spec.en.yaml`: shared contracts spec
- `structure/target-directory-structure.en.md`: target directory structure plan
