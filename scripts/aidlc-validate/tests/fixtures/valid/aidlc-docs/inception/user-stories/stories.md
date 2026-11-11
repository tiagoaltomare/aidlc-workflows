# Stories

### US-001 Checkout a book
As a member, I want to check out a book so that I can read it.
Requirement: REQ-001

**Acceptance Criteria:**

- Given I am a registered member
- When I checkout an available book
- Then the loan is created

- Given the book is already on loan
- When I checkout that book
- Then I see it is unavailable

### US-002 Browse catalog
As a member, I want to browse the catalog so that I can find a book.
Requirement: REQ-002

**Acceptance Criteria:**

- Given the catalog has books
- When I list titles
- Then I see available copies

- Given the catalog is empty
- When I list titles
- Then I see an empty list
