# Docitai Constitution

## Core Principles

### I.API-DRIVEN
The application have to be build using api driven and api-first approach, using OpenAPI specification definition. Backend and frontend implementations must strictly adhere to contract-defined interfaces. API contracts serve as the single source of truth for inter-service communication, data models, and validation rules

### II. Development Order
Development should be approached in a phased manner, develop the api's first and then develop the frontend applications.

### III. Development Methodology
Dont use TDD, since this is single person project, try to adhere to mix of vibe and spec driven approach. - DONT write unit test cases, or Integration test cases as part of the development. 

### IV. Application Design Patterns
Strictly follow DDD for line business applications, and EDA approach. every backend services needs to have repository pattern followed and a clean architectural style.

## Technical Constraints
The below are the set of technologies and libraries to be used across the applications in the monorepo

## Repository and Package Management
- Monorepo based on pnpm workspaces.
- Should follow workspace structure based on `nx` - only take inspiration 

## Technical Stack
- Backend: Nestjs (fastify)
- Frontend: Nextjs
- UI Libraries: shadcn.ui, radix-ui, chartjs, tailwind.
- ORM: Prisma
- Database: Postgres
- Auth:	OAuth2/OpenID Connect (support passport js), Custom JWT token (support for SSO) 
- Permission: OpenFGA for relationship based authorization model

## Security and Compliance
- Encryption: At rest and in transit.
- Authentication: JWT-based, with tenant context.
- Authorization: Role and ACL-based.
- Compliance: GDPR, HIPAA (if applicable).

## Governance
All PRs/reviews must verify compliance; Complexity must be justified; 

**Version**: 1.0 | **Ratified**: 2025-09-12 | **Last Amended**: 2025-09-12
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->