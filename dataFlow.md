```mermaid
flowchart LR

    A[API Alpha Vantage]
    B1[Extract Daily Data]
    B2[Extract Overview Data]
    C[Save Raw JSON]
    D[(SQL Server Staging)]
    E[Transform]
    H[(SQL Server Data Warehouse)]
    I([End])

    A --> B1
    A --> B2
    B1 --> C
    B2 --> C
    C --> D
    D --> E
    E --> H
    H --> I

    B1 -. Log .-> L[(Logging)]
    B2 -. Log .-> L
    C -. Log .-> L
    D -. Log .-> L
    E -. Log .-> L
    H -. Log .-> L
```