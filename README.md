# 🚉 Home Assistant – Next Train Voice Assistant (POC)

This repository contains a **Proof of Concept (POC)** that connects  
[Home Assistant](https://www.home-assistant.io/), [Ollama](https://ollama.ai/), and a custom [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server to provide **real-time train departure times** using voice commands.

---

## ✨ Overview

The project demonstrates how to combine:

- **Home Assistant Voice Assistant** → natural voice input  
- **Ollama LLM** → contextual conversation agent  
- **MCP Server (Python)** → custom tool `idf_stop_monitoring`  
- **Île-de-France Mobilité API** → real-time train departure data  

### Example Use Case

> **User:** “Hey Home Assistant, when is the next train to xxxx?”  
>
> **HA Voice Assistant** → Conversation Agent (Ollama) → MCP tool → Île-de-France Mobilité API → returns next departures → Ollama contextualizes → Voice Assistant replies with real-time info.  

---

## 🏗️ Architecture

The system runs inside a **Proxmox** host with multiple VMs:

```mermaid
flowchart TB
    %% Infrastructure
    subgraph Proxmox[Proxmox Server]
        
        %% LLM VM
        subgraph LLM_VM[VM: LLM Host]
            Ollama[Ollama LLM]
        end

        %% Debian Services VM
        subgraph Debian_VM[VM: Debian Services]
            MCP_Server[MCP Server: idf_stop_monitoring]
        end

        %% Home Assistant VM
        subgraph HA_VM[VM: Home Assistant]
            HA_Voice[Voice Assistant]
            HA_Agent[Conversation Agent]
            HA_Ollama[Ollama Integration]
            HA_MCP[MCP Integration]
        end
    end

    %% External API
    IDFM_API[Île-de-France Mobilité API]

    %% Relationships
    HA_Voice -->|"Ask: Next train?"| HA_Agent
    HA_Agent --> HA_Ollama
    HA_Agent --> HA_MCP
    HA_MCP --> MCP_Server
    MCP_Server --> IDFM_API
    IDFM_API --> MCP_Server
    MCP_Server --> HA_MCP
    HA_MCP --> HA_Agent
    HA_Ollama --> Ollama
    HA_Agent -->|"Answer"| HA_Voice
