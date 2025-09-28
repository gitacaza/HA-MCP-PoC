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

            %% Wyoming Protocol Integration
            subgraph Wyoming[Wyoming Protocol Integration]
                FastWhisper[fast-whisper (STT)]
                Piper[piper (TTS)]
                OpenWakeWord[openWakeWord (Wake word detection)]
            end
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

    %% Wyoming flows
    HA_Voice --> Wyoming
    Wyoming --> FastWhisper
    Wyoming --> Piper
    Wyoming --> OpenWakeWord
```
---

## ⚙️ Components

- **Proxmox Server** → Virtualization layer hosting all VMs  
- **VM: LLM Host** → runs Ollama LLM backend  
- **VM: Debian Services** → runs the MCP server (`idf_stop_monitoring_server.py`)  
- **VM: Home Assistant** → runs:
  - MCP integration (talks to MCP server)  
  - Ollama integration (talks to Ollama VM)  
  - Conversation Agent (links tools + LLM)  
  - Voice Assistant (user-facing)  

---

## 🚀 Setup (High-Level)

1. **Proxmox VM deployment**
   - Create 3 VMs: Ollama host, Debian services, Home Assistant  

2. **Ollama VM**
   - Install Ollama  
   - Expose API (default port `11434`)  

3. **Debian Services VM**
   - Clone this repo  
   - Setup Python venv & dependencies  
   - Run `idf_stop_monitoring_server.py` (MCP server)  
   - Ensure it can reach the Île-de-France Mobilité API  

4. **Home Assistant VM**
   - Add **MCP integration** → point to Debian MCP server  
   - Add **Ollama integration** → point to Ollama VM  
   - Create a **Conversation Agent** using `idf_stop_monitoring` tool  
   - Attach the **Voice Assistant** to the agent  

---

## 📌 Status

- ✅ Working as Proof of Concept  
- ⚠️ Not production-ready (no auth, limited error handling)  
- 🎯 Next steps:  
  - Add authentication / API key management  
  - Dockerize MCP server  
  - Improve multi-station & multi-destination support  

---

## 📜 License

MIT License – feel free to use, share, and adapt.  

---

## 🙌 Acknowledgments

- [Île-de-France Mobilité API](https://www.iledefrance-mobilites.fr/) for open transport data  
- [Model Context Protocol](https://modelcontextprotocol.io/) community  
- [Home Assistant](https://www.home-assistant.io/) and [Ollama](https://ollama.ai/) teams  




