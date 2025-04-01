flowchart TD
    %% Entrada principal
    START([Mensaje de WhatsApp]) --> WR[routes/whatsapp_routes.py\nprocess_whatsapp_message]
    WR --> IC[chains/intent_classifier.py\nIntentClassifier.predict]
    IC --> CG[graphs/main_graph.py\ncreate_conversation_graph]
    
    %% Grafo Principal
    subgraph "Main Conversation Graph"
        DETECT("DETECT_INTENTS\ndetect_intents()") --> ROUTER{route_from_detect_intents}
        ROUTER -->|"Nivel 1+\n[direccion, horario, etc.]"| GENERAL("GENERAL_INQUIRY\nhandle_general_inquiry()")
        ROUTER -->|"Nivel 3\n[estado_alarma]"| ALARM("ALARM_STATUS\nhandle_alarm_status()")
        ROUTER -->|"Nivel 3\n[escaneo_camaras]"| CAMERA("CAMERA_SCAN\nhandle_camera_scan()")
        ROUTER -->|"Nivel 2+\n[problema_alarma]"| START_T("START_TROUBLESHOOTING\nstart_troubleshooting()")
        ROUTER -->|"troubleshooting_active=true"| TROUBLE("TROUBLESHOOTING\nprocess_troubleshooting()")
        ROUTER -->|"Default"| LLM("LLM_RESPONSE\nhandle_llm_response()")
        
        START_T --> TROUBLE
        
        GENERAL --> DETECT
        ALARM --> DETECT
        CAMERA --> DETECT
        TROUBLE --> DETECT
        LLM --> DETECT
    end
    
    %% Grafo de Troubleshooting
    subgraph "Troubleshooting Graph"
        T_CONFIRM("CONFIRMATION\nconfirmation_step()") --> T_ROUTER{router}
        T_ROUTER -->|"user: sí, quiero"| T_KEYBOARD("KEYBOARD_SELECTION\nkeyboard_selection()")
        T_ROUTER -->|"user: no, salir"| T_EXIT("EXIT\nexit_flow()")
        
        T_KEYBOARD --> T_ROUTER
        T_ROUTER -->|"selected keyboard"| T_PROCESS_K("PROCESS_KEYBOARD\nprocess_keyboard_selection()")
        
        T_PROCESS_K --> T_ROUTER
        T_ROUTER -->|"direct_support=true"| T_EXIT
        T_ROUTER -->|"valid keyboard"| T_PROCESS_P("PROCESS_PROBLEM\nprocess_problem_selection()")
        
        T_PROCESS_P --> T_ROUTER
        T_ROUTER -->|"problem selected"| T_RATING("PROCESS_RATING\nprocess_rating()")
        
        T_RATING --> T_ROUTER
        T_ROUTER -->|"rating received"| T_EXIT
        T_ROUTER -->|"new problem"| T_CONFIRM
    end
    
    %% Conexión entre los grafos
    TROUBLE -.-> T_CONFIRM
    T_EXIT -.-> DETECT
    
    %% Final
    GENERAL --> RESP([Respuesta al Usuario])
    ALARM --> RESP
    CAMERA --> RESP
    LLM --> RESP
    T_EXIT --> RESP
    
    %% Estilos
    classDef mainNode fill:#c4e3f3,stroke:#5bc0de,stroke-width:2px
    classDef troubleNode fill:#d9edf7,stroke:#31708f,stroke-width:1px
    classDef routerNode fill:#fcf8e3,stroke:#faebcc,stroke-width:2px
    classDef entryNode fill:#d6e9c6,stroke:#3c763d,stroke-width:2px
    classDef exitNode fill:#f2dede,stroke:#ebccd1,stroke-width:2px
    
    class DETECT,GENERAL,ALARM,CAMERA,START_T,TROUBLE,LLM mainNode
    class T_CONFIRM,T_KEYBOARD,T_PROCESS_K,T_PROCESS_P,T_RATING troubleNode
    class ROUTER,T_ROUTER routerNode
    class START,WR,IC,CG entryNode
    class T_EXIT,RESP exitNode