Feature: Customer Support Agent
  As a customer support system
  I want to handle customer requests accurately
  So that customers get fast and correct resolutions

  Scenario: Standard refund happy path
    Given a customer with ID "CUST-001"
    When they request a refund for order "ORD-001"
    Then the refund should be approved
    And the response should contain "89.99"
    And no escalation should occur

  Scenario: High value refund policy enforcement
    Given a customer with ID "CUST-004"
    When they request a refund for order "ORD-005"
    Then the case should be escalated to a human
    And the response should contain "escalat"