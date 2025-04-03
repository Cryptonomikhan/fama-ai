flowchart TD
    A[Obtain API Key] --> B[API Key Authentication]
    B --> C[Submit Investment Vehicle Description and Parameters]
    C --> D[Start Multi-Agent Workflow]
    D --> E[Invoke Research Agent]
    D --> F[Invoke Modeling Agent]
    D --> G[Invoke Scenario Planner Agent]
    D --> H[Invoke Assumption Generator Agent]
    D --> I[Invoke Validator Reviewer Agent]
    E --> J[Aggregate Research Findings]
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K[Compile Comprehensive Financial Model]
    K --> L[Generate Report in JSON, CSV, PDF or Dashboard]
    L --> M[Return Final Output via API]
    M --> N[Stream Logs for Monitoring and Debugging]
    O[Manage API Settings and Account Preferences] --- B
    P[Error Handling and Retry Mechanism] --- E
    P --- F
    P --- G
    P --- H
    P --- I
    P --> Q[Notify User and Offer Retry Options]
    Q --> D