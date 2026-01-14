Feature: Production Deployment
  Deploy bot to Yandex Cloud Serverless Container

  Scenario: Build Docker image
    Given Dockerfile exists
    When I build Docker image
    Then image should be created successfully
    And image should be tagged with version

  Scenario: Push to Container Registry
    Given Docker image is built
    When I push to Yandex Container Registry
    Then image should be available in registry

  Scenario: Deploy to Serverless Container
    Given image is in registry
    When I deploy new revision
    Then container should be running
    And health check should pass

  Scenario: Configure Telegram Webhook
    Given container is deployed
    When I set Telegram webhook URL
    Then webhook should be configured
    And bot should receive messages
