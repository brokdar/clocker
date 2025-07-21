# Comprehensive Code Documentation Generator

Analyze and document the code at path: $ARGUMENTS

## Documentation Objectives

You are tasked with creating comprehensive developer documentation that serves as the primary entry point for understanding this codebase. The documentation should enable developers and Claude Code to quickly grasp the system's architecture, design patterns, and implementation details.

## Analysis Steps

### 1. Initial Code Analysis

- Identify the type of project (application, library, service, etc.)
- Determine the primary programming language(s) and frameworks
- Scan for configuration files (package.json, requirements.txt, pom.xml, etc.)
- Identify the project structure and directory organization
- Detect build tools and dependency management systems

### 2. Architecture Analysis

- Identify the overall software architecture pattern (MVC, microservices, hexagonal, etc.)
- Map out the high-level components and their relationships
- Identify layers (presentation, business logic, data access, etc.)
- Detect integration points with external systems
- Analyze data flow patterns

### 3. Design Pattern Identification

- Catalog design patterns used (Factory, Observer, Strategy, etc.)
- Identify architectural patterns (Repository, Service Layer, etc.)
- Note any domain-driven design concepts
- Highlight any anti-patterns that should be refactored

### 4. Dependency Analysis

- Map all external dependencies and their versions
- Identify internal module dependencies
- Create a dependency graph showing relationships
- Flag any circular dependencies or tight coupling
- Note security vulnerabilities in dependencies if apparent

### 5. Code Structure Deep Dive

- Document the purpose of each major module/package
- Identify entry points and main execution flows
- Map API endpoints, command handlers, or event listeners
- Document configuration options and environment variables
- Analyze error handling and logging strategies

### 6. Algorithm Documentation

For complex algorithms:

- Provide detailed textual explanation
- Include Big O complexity analysis
- Document edge cases and limitations
- Create activity diagrams for step-by-step visualization

### 7. Integration Documentation

For external integrations:

- Document all external APIs or services used
- Map authentication and authorization flows
- Create sequence diagrams for complex interactions
- Note rate limits, timeouts, and retry strategies

## Documentation Output Format

Create a markdown file named `README.md` in the appropriate location:

- For a file: Create `<filename>.md` in the same directory
- For a directory: Create `README.md` inside that directory

The documentation should follow this structure:

```markdown
# [Project/Module Name] Documentation

## Overview
Brief description of what this code does and its purpose.

## Quick Start
Essential information for developers to start working with this code.

## Architecture

### System Architecture
[Mermaid diagram showing high-level architecture]

### Key Components
- Component descriptions with responsibilities

### Design Patterns
- Patterns used and their implementation

## Dependencies

### External Dependencies
[Table or list of external dependencies without versions]

### Internal Dependencies
[Mermaid diagram showing internal module relationships]

## Code Structure

### Directory Structure

```txt
project/
├── src/
│   ├── components/
│   └── ...

```

### Module Descriptions

Detailed description of each major module/package

## Core Functionality

### Main Flows

[Sequence diagrams for primary use cases]

### Algorithms

[Activity diagrams and explanations for complex algorithms]

### API Reference

If applicable, document APIs with examples

## Configuration

Environment variables, config files, and their purposes

## Integration Points

External services, APIs, and how they're integrated

## Development Guidelines

- Coding standards followed
- Testing approach
- Build and deployment process

## Security Considerations

Authentication, authorization, and security measures

## Performance Considerations

Caching strategies, optimization techniques

## Known Issues and TODOs

Current limitations or planned improvements

## Glossary

Domain-specific terms and concepts

```

## Visualization Requirements

### Mermaid Diagrams to Include

1. **Architecture Diagram** (graph or C4 diagram)

   ```mermaid
   graph TB
     subgraph "System Architecture"
       ...
     end
   ```

2. **Dependency Graph**

   ```mermaid
   graph LR
     ModuleA --> ModuleB
     ...
   ```

3. **Sequence Diagrams** for complex interactions

   ```mermaid
   sequenceDiagram
     participant Client
     participant Server
     ...
   ```

4. **Activity Diagrams** for complex algorithms

   ```mermaid
   graph TD
     Start([Start]) --> Step1
     ...
   ```

5. **Class Diagrams** for OOP systems (if applicable)

   ```mermaid
   classDiagram
     class ClassName {
       ...
     }
   ```

## Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Provide context for design decisions
- Link to relevant external documentation
- Use consistent formatting and terminology
- Include timestamps for time-sensitive information

## Post-Documentation Tasks

After creating the documentation:

1. Check if `@CLAUDE.md` exists at the project root
2. If it exists, add a reference to the new documentation using @-syntax:
   - For file documentation: `@<path/to/filename>.DOCUMENTATION.md`
   - For directory documentation: `@<path/to/directory>/DOCUMENTATION.md`
3. If `@CLAUDE.md` doesn't exist, suggest creating it with appropriate references

## Important Notes

- Focus on information that helps developers understand and work with the code
- Prioritize clarity over completeness - highlight what's most important
- Make the documentation scannable with clear headings and visual aids
- Ensure all diagrams are properly rendered and labeled
- Test any code examples included in the documentation
- Keep security-sensitive information appropriately abstracted

Remember: This documentation should be the go-to resource for anyone needing to understand, maintain, or extend this codebase. Make it comprehensive yet accessible.
