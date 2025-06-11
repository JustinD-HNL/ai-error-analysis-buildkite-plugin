# Usage Examples

Real-world examples of using the AI Error Analysis Buildkite Plugin across different scenarios and tech stacks.

## Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Technology Stack Examples](#technology-stack-examples)
- [Deployment Pipeline Examples](#deployment-pipeline-examples)
- [Advanced Configuration Examples](#advanced-configuration-examples)
- [Enterprise Examples](#enterprise-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

## Quick Start Examples

### Minimal Setup

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0: ~
```

**Environment:**
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```

### Basic Configuration

```yaml
steps:
  - command: "pytest tests/"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4o-mini
          conditions:
            branches: ["main", "develop"]
```

### Multiple Providers

```yaml
steps:
  - command: "cargo test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4o-mini
            - name: claude
              model: claude-3-haiku-20240307
          performance:
            fallback_strategy: priority
```

## Technology Stack Examples

### Node.js / JavaScript

```yaml
steps:
  - label: "🧪 Node.js Tests"
    command: |
      npm ci
      npm run test:unit
      npm run test:integration
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Node.js application using:
              - Express.js framework
              - Jest for testing
              - PostgreSQL database
              - Redis for caching
          advanced:
            custom_prompts:
              test_failure: |
                Analyze this Node.js test failure. Common issues include:
                1. Async/await problems and Promise handling
                2. Database connection issues
                3. Mock setup problems
                4. Environment variable configuration
```

### Python / Django

```yaml
steps:
  - label: "🐍 Python Tests"
    command: |
      pip install -r requirements.txt
      python manage.py test
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Django web application with:
              - PostgreSQL database
              - Celery for background tasks
              - Redis for caching and message broker
              - pytest for testing
          advanced:
            custom_prompts:
              test_failure: |
                Analyze this Django test failure. Focus on:
                1. Database migration issues
                2. Django settings configuration
                3. Import path problems
                4. Fixture and factory setup
```

### Java / Spring Boot

```yaml
steps:
  - label: "☕ Java Build"
    command: |
      ./mvnw clean compile
      ./mvnw test
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Spring Boot application using:
              - Maven for build management
              - JUnit 5 for testing
              - Spring Data JPA
              - MySQL database
          advanced:
            custom_prompts:
              compilation_error: |
                Analyze this Java compilation error. Common issues:
                1. Missing dependencies in pom.xml
                2. Import statement problems
                3. Version compatibility issues
                4. Annotation processing errors
```

### Go

```yaml
steps:
  - label: "🐹 Go Build"
    command: |
      go mod tidy
      go build ./...
      go test ./...
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Go microservice with:
              - Go modules for dependency management
              - PostgreSQL with pgx driver
              - gRPC API
              - Docker containerization
          advanced:
            custom_prompts:
              compilation_error: |
                Analyze this Go compilation error. Focus on:
                1. Module dependency issues
                2. Import path problems
                3. Interface implementation errors
                4. Type assertion failures
```

### Rust

```yaml
steps:
  - label: "🦀 Rust Build"
    command: |
      cargo build
      cargo test
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Rust application using:
              - Cargo for package management
              - Tokio for async runtime
              - Diesel for database ORM
              - Serde for serialization
          advanced:
            custom_prompts:
              compilation_error: |
                Analyze this Rust compilation error. Common issues:
                1. Borrowing and lifetime errors
                2. Type mismatches and trait bounds
                3. Dependency version conflicts
                4. Macro expansion problems
```

### React / Frontend

```yaml
steps:
  - label: "⚛️ React Build"
    command: |
      npm ci
      npm run build
      npm run test
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              React application using:
              - Create React App / Vite
              - TypeScript
              - Jest and React Testing Library
              - Webpack for bundling
          advanced:
            custom_prompts:
              compilation_error: |
                Analyze this React build error. Focus on:
                1. TypeScript type errors
                2. Import/export problems
                3. Webpack configuration issues
                4. Package version conflicts
```

## Deployment Pipeline Examples

### Docker Build Pipeline

```yaml
steps:
  - label: "🐳 Docker Build"
    command: |
      docker build -t myapp:${BUILDKITE_BUILD_NUMBER} .
      docker run --rm myapp:${BUILDKITE_BUILD_NUMBER} npm test
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Multi-stage Docker build for Node.js application:
              - Node.js 18 Alpine base image
              - Production optimization
              - Health checks included
          advanced:
            custom_prompts:
              compilation_error: |
                Analyze this Docker build failure. Common issues:
                1. Base image availability
                2. COPY/ADD path problems
                3. Dependency installation failures
                4. Permission issues
              deployment_error: |
                Analyze this container deployment error. Focus on:
                1. Image registry authentication
                2. Resource constraints
                3. Network connectivity
                4. Environment configuration
```

### Kubernetes Deployment

```yaml
steps:
  - label: "☸️ Deploy to K8s"
    command: |
      kubectl apply -f k8s/
      kubectl rollout status deployment/myapp
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              Kubernetes deployment includes:
              - Deployment with 3 replicas
              - Service and Ingress
              - ConfigMap and Secrets
              - HorizontalPodAutoscaler
          advanced:
            custom_prompts:
              deployment_error: |
                Analyze this Kubernetes deployment error. Focus on:
                1. Resource quota limitations
                2. Image pull failures
                3. ConfigMap/Secret mounting issues
                4. Service account permissions
                5. Network policy restrictions
```

### AWS Infrastructure

```yaml
steps:
  - label: "☁️ Deploy Infrastructure"
    command: |
      terraform plan
      terraform apply -auto-approve
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            custom_context: |
              AWS infrastructure using Terraform:
              - ECS Fargate services
              - Application Load Balancer
              - RDS PostgreSQL
              - ElastiCache Redis
              - CloudWatch monitoring
          advanced:
            custom_prompts:
              deployment_error: |
                Analyze this AWS deployment error. Common issues:
                1. IAM permission problems
                2. Security group configuration
                3. Resource limits and quotas
                4. Network ACL restrictions
                5. Service availability
```

## Advanced Configuration Examples

### Branch-Specific Analysis

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Detailed analysis for main branch
          conditions:
            branches: ["main"]
          ai_providers:
            - name: openai
              model: gpt-4o  # Premium model for main
          context:
            log_lines: 1000
            custom_context: "Critical production pipeline"

  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Basic analysis for feature branches
          conditions:
            branches: ["feature/*"]
          ai_providers:
            - name: openai
              model: gpt-4o-mini  # Cost-effective for features
          context:
            log_lines: 300
```

### Async Analysis for Fast Builds

```yaml
steps:
  - label: "🚀 Fast Tests"
    command: "npm run test:unit"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          performance:
            async_execution: true  # Don't block build
            timeout: 300
          output:
            annotation_context: "background-analysis"
```

### Multi-Environment Pipeline

```yaml
# Development Environment
- label: "🧪 Dev Tests"
  command: "npm test"
  env:
    NODE_ENV: development
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        conditions:
          branches: ["develop", "feature/*"]
        context:
          custom_context: "Development environment with mock services"

# Staging Environment  
- label: "🎭 Staging Tests"
  command: "npm run test:e2e"
  env:
    NODE_ENV: staging
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        conditions:
          branches: ["main", "release/*"]
        context:
          custom_context: "Staging environment with real external services"
        advanced:
          custom_prompts:
            test_failure: |
              Staging test failure. Consider:
              1. External service availability
              2. Data synchronization issues
              3. Environment-specific configuration
              4. Network connectivity problems

# Production Deployment
- label: "🚀 Production Deploy"
  command: "kubectl apply -f k8s/production/"
  env:
    ENVIRONMENT: production
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        trigger: always  # Analyze all production deployments
        ai_providers:
          - name: claude
            model: claude-3-opus-20240229  # Premium for production
        output:
          annotation_style: error
          save_as_artifact: true
          artifact_path: "production-analysis.json"
```

## Enterprise Examples

### Security-Focused Configuration

```yaml
steps:
  - command: "npm audit && npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Comprehensive security redaction
          redaction:
            redact_file_paths: true
            redact_urls: true
            custom_patterns:
              # Company-specific secrets
              - "(?i)acmecorp[_-]?api[_-]?key[\\s]*[=:]+[\\s]*[^\\s]+"
              - "(?i)internal[_-]?webhook[\\s]*[=:]+[\\s]*[^\\s]+"
              - "(?i)vault[_-]?token[\\s]*[=:]+[\\s]*[^\\s]+"
              
              # Database connections
              - "postgresql://[^\\s]+"
              - "mongodb://[^\\s]+"
              - "redis://[^\\s]+"
              
              # Authentication tokens
              - "Bearer [a-zA-Z0-9._-]+"
              - "jwt=[a-zA-Z0-9._-]+"
              - "session=[a-zA-Z0-9._-]+"
          
          # Additional security context
          context:
            custom_context: |
              Enterprise application with:
              - HashiCorp Vault for secrets
              - LDAP authentication
              - PCI DSS compliance requirements
              - SOC 2 Type II controls
```

### Multi-Team Configuration

```yaml
# Frontend Team
- label: "🎨 Frontend Build"
  command: "npm run build"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        output:
          annotation_context: "frontend-analysis"
        context:
          custom_context: "React SPA with TypeScript"
        advanced:
          custom_prompts:
            compilation_error: "Focus on TypeScript and React-specific issues"

# Backend Team
- label: "⚙️ Backend Build" 
  command: "mvn test"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        output:
          annotation_context: "backend-analysis"
        context:
          custom_context: "Spring Boot microservice"
        advanced:
          custom_prompts:
            test_failure: "Focus on Spring Boot and JPA-related issues"

# DevOps Team
- label: "🔧 Infrastructure"
  command: "terraform apply"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        output:
          annotation_context: "infrastructure-analysis"
        context:
          custom_context: "AWS infrastructure with Terraform"
        advanced:
          custom_prompts:
            deployment_error: "Focus on AWS and Terraform-specific issues"
```

### Cost-Optimized Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Use most cost-effective providers
          ai_providers:
            - name: gemini
              model: gemini-1.5-flash  # Very cost-effective
            - name: openai
              model: gpt-4o-mini       # Fallback option
          
          # Optimize context size
          context:
            log_lines: 200
            include_environment: false  # Reduce context
          
          # Aggressive caching
          performance:
            cache_enabled: true
            cache_ttl: 86400  # 24 hours
          
          # Only analyze critical failures
          conditions:
            exit_status: [1, 2]
            branches: ["main", "release/*"]
```

## Troubleshooting Examples

### Debug Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          advanced:
            debug_mode: true      # Detailed logging
            dry_run: true         # Test without API calls
            max_retries: 1        # Fail fast for debugging
          performance:
            timeout: 30           # Short timeout for testing
```

### Testing Different Providers

```yaml
# Test OpenAI
- label: "Test OpenAI"
  command: "echo 'ERROR: Test failure' && exit 1"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        ai_providers:
          - name: openai
            model: gpt-4o-mini
        output:
          annotation_context: "openai-test"

# Test Claude
- label: "Test Claude"
  command: "echo 'ERROR: Test failure' && exit 1"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        ai_providers:
          - name: claude
            model: claude-3-haiku-20240307
        output:
          annotation_context: "claude-test"

# Test Gemini
- label: "Test Gemini"
  command: "echo 'ERROR: Test failure' && exit 1"
  plugins:
    - your-org/ai-error-analysis#v1.0.0:
        ai_providers:
          - name: gemini
            model: gemini-1.5-flash
        output:
          annotation_context: "gemini-test"
```

### Performance Testing

```yaml
steps:
  - label: "Performance Test"
    command: |
      # Generate large log output
      for i in {1..1000}; do
        if [ $((i % 100)) -eq 0 ]; then
          echo "Line $i: ERROR: Performance test error $((i/100))"
        else
          echo "Line $i: Normal log output for performance testing"
        fi
      done
      exit 1
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          context:
            log_lines: 1000
          performance:
            timeout: 60
            cache_enabled: true
          advanced:
            debug_mode: true
```

### Error Pattern Testing

```yaml
steps:
  # Test compilation errors
  - label: "Test Compilation Error"
    command: |
      echo "src/main.cpp:42:15: error: expected ';' before 'return'"
      echo "Build failed with 1 error"
      exit 1
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          output:
            annotation_context: "compilation-test"

  # Test dependency errors  
  - label: "Test Dependency Error"
    command: |
      echo "npm ERR! Could not resolve dependency: package@1.0.0"
      echo "Module 'missing-package' not found"
      exit 1
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          output:
            annotation_context: "dependency-test"

  # Test network errors
  - label: "Test Network Error"
    command: |
      echo "curl: (7) Failed to connect to api.example.com port 443"
      echo "Connection timeout after 30 seconds"
      exit 1
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          output:
            annotation_context: "network-test"
```

These examples provide a comprehensive foundation for implementing the AI Error Analysis plugin across different scenarios, tech stacks, and organizational needs.