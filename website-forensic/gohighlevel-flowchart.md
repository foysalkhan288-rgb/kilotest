# GoHighLevel — Feature & Automation Flowchart (Mermaid)

Render this with any Mermaid viewer (GitHub, VS Code Mermaid preview, mermaid.live).

## A. Platform Architecture (modules -> sub-features)

```mermaid
flowchart TB
    GHL["GoHighLevel — All-in-One White-Label CRM/Automation"]
    
    subgraph CORE["CORE ENGINE"]
        CRM["CRM & Contacts\n(unlimited, custom objects)"]
        WF["Workflow Automation\n(30+ triggers / 14 action cats)"]
        INBOX["Unified Inbox\n(SMS/Email/Call/FB/IG/WA/GBM/LiveChat)"]
    end

    subgraph ACQUIRE["ACQUIRE"]
        FORM["Forms / Surveys / Quizzes"]
        FUN["Funnels & Websites\n(AI builder)"]
        ADS["Ad Lead Forms\n(FB / Google / TikTok / LinkedIn)"]
        WA["WhatsApp / Click-to-WA Ads"]
    end

    subgraph COMM["COMMUNICATE"]
        SMS["LC Phone / SMS / MMS"]
        EMAIL["LC Email & Drip"]
        VOICE["Voice AI\n(19 langs, 340 voices)"]
        CONV["Conversation AI\n(multi-channel LLM bot)"]
        CONTENT["Content AI\n(copy generation)"]
    end

    subgraph CONVERT["CONVERT"]
        PIPE["Pipelines & Opportunities\n(Revenue Forecasting)"]
        CAL["Calendars & Booking"]
        DOC["Documents & Contracts\n(e-sign)"]
        PAY["Payments\n(Stripe/PayPal/Orders/Invoices)"]
    end

    subgraph RETAIN["RETAIN & SCALE"]
        REP["Reputation\n(Review AI / Video Testimonials)"]
        MEM["Memberships / Courses / Communities"]
        AFF["Affiliate Manager + Program\n(40% recurring)"]
        SOCIAL["Social Planner"]
    end

    subgraph AI["AI LAYER"]
        AGENT["Agent Studio / Eliza"]
        ASK["Ask AI\n(blog/voice/memory)"]
        IMG["AI Image Recognition"]
    end

    subgraph CONFIG["DELIVERY / ADMIN"]
        WL["White-Label & SaaS Mode\n(Stripe Tax, Rebilling)"]
        ROLE["Roles / Multi-Location"]
        API["API v2 + Webhooks + Marketplace 1500+ apps"]
    end

    GHL --> CORE
    GHL --> ACQUIRE
    GHL --> COMM
    GHL --> CONVERT
    GHL --> RETAIN
    AI -.powers.-> COMM
    AI -.powers.-> CORE
    CONFIG -.governs.-> GHL
```

## B. Lead Journey (a real automation flow)

```mermaid
flowchart TD
    L["New Lead"] --> SRC{"Source?"}
    SRC -->|"FB/Lead Ad"| FB["Facebook Lead Form Submitted"]
    SRC -->|"Website"| FM["Form / Survey Submitted"]
    SRC -->|"Call"| CALL["Inbound Call / Missed Call"]

    FB --> WF
    FM --> WF
    CALL -->|"Missed"| MCTB["Missed-Call Text Back (SMS)"]
    CALL -->|"Answered by Voice AI"| VAB["Voice AI qualifies + books"]

    WF["Workflow Trigger"] --> SPEED["Wait 10s -> Speed-to-Lead\nSMS + Email"]
    SPEED --> TAG["Add Tag + Create Opportunity (New Lead)"]
    TAG --> CONVAI{"After hours?"}
    CONVAI -->|"Yes"| BOT["Conversation AI handles Q&A + books"]
    CONVAI -->|"No"| HUMAN["Route to assigned user"]

    BOT --> APPT["Appointment Booked"]
    HUMAN --> APPT
    VAB --> APPT
    MCTB --> APPT

    APPT --> REM["Appointment Reminder Sequence\n(SMS/Email/Voice reminder)"]
    REM --> SH{"Show / No-show?"}
    SH -->|"Shown"| DONE["Mark Completed -> Send Review Request\n(Review AI drafts reply)"]
    SH -->|"No-show"| NOSHOW["No-Show Recovery workflow"]
    NOSHOW --> REM

    DONE --> UPSELL["Add to Course/Community\nor Affiliate Program"]
    UPSELL --> LOYAL["Loyalty / Referral loop"]
```
