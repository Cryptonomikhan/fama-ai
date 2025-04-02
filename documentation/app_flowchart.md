flowchart TD
    API_Request[API Request: User/app initiates with business context \n and financial data]
    Data_Security[Data Security: Transient processing and secure API calls]
    Data_Aggregation[Integration & Data Aggregation: Connect to Plaid and other financial sources]
    Deep_Research[Deep Research & Analysis: Market research and revenue model options]
    Multi_Agent[Multi-Agent Coordination: Communication between research, modeling, \n and reporting agents]
    Financial_Model[Financial Model Construction: Build financial models \n using gathered data & insights]
    Dashboard_Generation[Dashboard Generation & Visualization: White-label dashboards \n and customizable reports]
    Report_Delivery[Report Delivery: Return model and visualizations via API]
    Settings[Settings & Account Management: Handled externally via API config]
    Error_Handler[Error Handler: Graceful fallback for API errors and integration issues]

    API_Request --> Data_Security
    Data_Security --> Data_Aggregation
    Data_Aggregation --> Deep_Research
    Deep_Research --> Multi_Agent
    Multi_Agent --> Financial_Model
    Financial_Model --> Dashboard_Generation
    Dashboard_Generation --> Report_Delivery

    API_Request --> Settings

    Data_Aggregation -- Error --> Error_Handler
    Deep_Research -- Error --> Error_Handler
    Financial_Model -- Error --> Error_Handler
    Dashboard_Generation -- Error --> Error_Handler