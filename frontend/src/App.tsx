
import { useEffect, useState } from 'react'
import {
  ShieldCheck, Search, Link2, MessageSquareWarning, Activity,
  History, AlertTriangle, Languages, RefreshCw, Info, MessagesSquare,
} from 'lucide-react'

const API = 'http://127.0.0.1:8000'

type Language = 'en' | 'kn' | 'hi'
type Mode = 'message' | 'conversation' | 'url'
type Channel = 'sms' | 'email' | 'chat'

type Result = {
  category: string
  risk_score: number
  explanation: string[]
  recommendation: string
  model_prediction?: string | null
  model_used?: boolean
  model_status?: string
  input_mode?: string
  classifier_score?: number | null
  classifier_threshold?: number | null
  classifier_model?: string | null
  legacy_model_used?: boolean
  legacy_spam_score?: number | null
}

type HistoryItem = {
  id: number
  input_type: string
  category: string
  risk_score: number
}

const translations = {
  en: {
    prototype: 'Prototype dashboard',
    eyebrow: 'AI-ASSISTED FRAUD AWARENESS',
    headline: 'Pause. Check. Stay safe.',
    subtitle: 'Review suspicious messages, conversations and links before taking action.',
    analysis: 'THREAT ANALYSIS',
    check: 'Check a message or URL',
    message: 'Single message',
    conversation: 'Full conversation',
    url: 'URL',
    messageLabel: 'Paste a suspicious message',
    conversationLabel: 'Paste the full conversation',
    urlLabel: 'Enter a suspicious URL — do not open it',
    messagePlaceholder: 'Example: Your bank account will be blocked. Verify your KYC...',
    conversationPlaceholder: 'Paste the complete chat or message thread here...',
    urlPlaceholder: 'https://example.com/...',
    channel: 'Message channel',
    sms: 'SMS',
    email: 'Email',
    chat: 'Chat',
    modeMessageHint: 'Analyze one message on its own.',
    modeConversationHint: 'Analyze the complete conversation together. Channel is set to Chat.',
    modeUrlHint: 'The URL is checked locally. The submitted link is not opened.',
    privacy: 'Never enter OTPs, passwords, PINs or banking secrets.',
    analyze: 'Analyze safely',
    analyzing: 'Analyzing...',
    assessment: 'ASSESSMENT',
    why: 'Why it was flagged',
    recommendation: 'Safety recommendation',
    model: 'Detection model',
    modelUsed: 'BSIS classifier used',
    modelSkipped: 'BSIS classifier was not used',
    prediction: 'Model prediction',
    scam: 'Scam',
    notFlagged: 'Not flagged by model',
    spam: 'Spam',
    ham: 'Likely legitimate',
    classifierScore: 'Raw classifier score',
    threshold: 'Decision threshold',
    classifierModel: 'Classifier',
    legacyUsed: 'Legacy English SMS model also used',
    legacySkipped: 'Legacy English SMS model not used',
    legacyScore: 'Legacy spam score',
    noModel: 'No model prediction available',
    rawScoreNote: 'Raw classifier score, not a calibrated probability.',
    safety: 'Safety first',
    safetyText: 'Never share OTPs, passwords or PINs.',
    verify: 'Verify independently',
    verifyText: 'Use official apps and known contact details.',
    recent: 'Recent checks',
    refresh: 'Refresh',
    empty: 'Your recent checks appear here after analysis.',
    footer: 'Educational prototype · Verify unexpected requests independently.',
    lower: 'Lower risk',
    caution: 'Needs caution',
    high: 'High risk',
    error: 'Could not connect to the backend. Check that the API server is running.',
    invalid: 'Enter at least 3 characters to analyze.',
    safeNote: 'A low score does not prove that a message or link is safe.',
    heuristic: 'Heuristic risk indicator, not a calibrated fraud probability or definitive verdict.',
    otp: 'Mentions an OTP or one-time password',
    urgency: 'Uses urgency or pressure',
    kyc: 'Requests account or KYC verification',
    prize: 'Promises a prize or reward',
    fee: 'Requests an upfront fee',
    link: 'Contains a web link',
    noPattern: 'No configured warning pattern was detected',
    https: 'URL does not use HTTPS',
    hostname: 'Hostname format looks unusual',
    ip: 'Uses a raw IP address instead of a domain',
    longHost: 'Unusually long hostname',
    hyphens: 'Hostname contains several hyphens',
    at: 'Contains an @ symbol that may obscure the destination',
    keyword: 'Contains a sensitive-account keyword; this alone does not prove fraud',
    noUrlPattern: 'No basic URL warning signal was detected',
    advice: 'Do not click links or share OTPs, passwords or payment details. Verify independently using the official app or phone number.',
    safeAdvice: 'No strong warning pattern was found. This does not prove the message is safe; verify unexpected requests independently.',
    urlAdvice: 'Do not open suspicious links. Check the domain independently and use the official website or app.',
    urlHeuristic: 'URL analysis uses local heuristic checks, not the BSIS message classifier.',
    historyMessage: 'Message',
    historyConversation: 'Conversation',
    historyUrl: 'URL',
    language: 'Language',

  },
  kn: {
    prototype: 'ಮಾದರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    eyebrow: 'AI ಆಧಾರಿತ ವಂಚನೆ ಜಾಗೃತಿ',
    headline: 'ನಿಲ್ಲಿಸಿ. ಪರಿಶೀಲಿಸಿ. ಸುರಕ್ಷಿತರಾಗಿರಿ.',
    subtitle: 'ಕ್ರಮ ಕೈಗೊಳ್ಳುವ ಮೊದಲು ಅನುಮಾನಾಸ್ಪದ ಸಂದೇಶಗಳು, ಸಂಭಾಷಣೆಗಳು ಮತ್ತು ಲಿಂಕ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.',
    analysis: 'ಅಪಾಯ ವಿಶ್ಲೇಷಣೆ',
    check: 'ಸಂದೇಶ ಅಥವಾ URL ಪರಿಶೀಲಿಸಿ',
    message: 'ಒಂದು ಸಂದೇಶ',
    conversation: 'ಪೂರ್ಣ ಸಂಭಾಷಣೆ',
    url: 'URL',
    messageLabel: 'ಅನುಮಾನಾಸ್ಪದ ಸಂದೇಶವನ್ನು ಇಲ್ಲಿ ಹಾಕಿ',
    conversationLabel: 'ಪೂರ್ಣ ಸಂಭಾಷಣೆಯನ್ನು ಇಲ್ಲಿ ಹಾಕಿ',
    urlLabel: 'ಅನುಮಾನಾಸ್ಪದ URL ನಮೂದಿಸಿ — ತೆರೆಯಬೇಡಿ',
    messagePlaceholder: 'ಉದಾಹರಣೆ: ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ನಿರ್ಬಂಧಿಸಲಾಗುತ್ತದೆ. KYC ಪರಿಶೀಲಿಸಿ...',
    conversationPlaceholder: 'ಸಂಪೂರ್ಣ ಚಾಟ್ ಅಥವಾ ಸಂದೇಶಗಳ ಸರಣಿಯನ್ನು ಇಲ್ಲಿ ಹಾಕಿ...',
    urlPlaceholder: 'https://example.com/...',
    channel: 'ಸಂದೇಶದ ಮಾಧ್ಯಮ',
    sms: 'SMS',
    email: 'ಇಮೇಲ್',
    chat: 'ಚಾಟ್',
    modeMessageHint: 'ಒಂದು ಸಂದೇಶವನ್ನು ಪ್ರತ್ಯೇಕವಾಗಿ ವಿಶ್ಲೇಷಿಸಿ.',
    modeConversationHint: 'ಪೂರ್ಣ ಸಂಭಾಷಣೆಯನ್ನು ಒಟ್ಟಿಗೆ ವಿಶ್ಲೇಷಿಸಿ. ಮಾಧ್ಯಮವನ್ನು ಚಾಟ್ ಎಂದು ಹೊಂದಿಸಲಾಗಿದೆ.',
    modeUrlHint: 'URL ಅನ್ನು ಸ್ಥಳೀಯವಾಗಿ ಪರಿಶೀಲಿಸಲಾಗುತ್ತದೆ. ಲಿಂಕ್ ತೆರೆಯುವುದಿಲ್ಲ.',
    privacy: 'OTP, ಪಾಸ್‌ವರ್ಡ್, PIN ಅಥವಾ ಬ್ಯಾಂಕಿಂಗ್ ರಹಸ್ಯಗಳನ್ನು ನಮೂದಿಸಬೇಡಿ.',
    analyze: 'ಸುರಕ್ಷಿತವಾಗಿ ವಿಶ್ಲೇಷಿಸಿ',
    analyzing: 'ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...',
    assessment: 'ಮೌಲ್ಯಮಾಪನ',
    why: 'ಎಚ್ಚರಿಕೆ ನೀಡಿದ ಕಾರಣಗಳು',
    recommendation: 'ಸುರಕ್ಷತಾ ಸಲಹೆ',
    model: 'ಪತ್ತೆಹಚ್ಚುವ ಮಾದರಿ',
    modelUsed: 'BSIS ಮಾದರಿಯನ್ನು ಬಳಸಲಾಗಿದೆ',
    modelSkipped: 'BSIS ಮಾದರಿಯನ್ನು ಬಳಸಿಲ್ಲ',
    prediction: 'ಮಾದರಿಯ ಫಲಿತಾಂಶ',
    scam: 'ವಂಚನೆ ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ',
    notFlagged: 'ಮಾದರಿಯಿಂದ ಗುರುತಿಸಲಾಗಿಲ್ಲ',
    spam: 'ಸ್ಪ್ಯಾಮ್',
    ham: 'ಬಹುಶಃ ಸಾಮಾನ್ಯ ಸಂದೇಶ',
    classifierScore: 'ಕಚ್ಚಾ ವರ್ಗೀಕರಣ ಸ್ಕೋರ್',
    threshold: 'ನಿರ್ಧಾರ ಮಿತಿ',
    classifierModel: 'ವರ್ಗೀಕರಣ ಮಾದರಿ',
    legacyUsed: 'ಹಳೆಯ ಇಂಗ್ಲಿಷ್ SMS ಮಾದರಿಯನ್ನೂ ಬಳಸಲಾಗಿದೆ',
    legacySkipped: 'ಹಳೆಯ ಇಂಗ್ಲಿಷ್ SMS ಮಾದರಿಯನ್ನು ಬಳಸಿಲ್ಲ',
    legacyScore: 'ಹಳೆಯ ಮಾದರಿಯ ಸ್ಪ್ಯಾಮ್ ಸ್ಕೋರ್',
    noModel: 'ಮಾದರಿಯ ಫಲಿತಾಂಶ ಲಭ್ಯವಿಲ್ಲ',
    rawScoreNote: 'ಇದು ಕಚ್ಚಾ ಮಾದರಿ ಸ್ಕೋರ್ ಮಾತ್ರ; ಪ್ರಮಾಣೀಕೃತ ಸಂಭವನೀಯತೆ ಅಲ್ಲ.',
    safety: 'ಸುರಕ್ಷತೆಯೇ ಮೊದಲು',
    safetyText: 'OTP, ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ PIN ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.',
    verify: 'ಸ್ವತಂತ್ರವಾಗಿ ಪರಿಶೀಲಿಸಿ',
    verifyText: 'ಅಧಿಕೃತ ಆ್ಯಪ್‌ಗಳು ಮತ್ತು ಪರಿಚಿತ ಸಂಪರ್ಕ ವಿವರಗಳನ್ನು ಬಳಸಿ.',
    recent: 'ಇತ್ತೀಚಿನ ಪರಿಶೀಲನೆಗಳು',
    refresh: 'ಮರುಲೋಡ್',
    empty: 'ವಿಶ್ಲೇಷಣೆಯ ನಂತರ ನಿಮ್ಮ ಇತ್ತೀಚಿನ ಪರಿಶೀಲನೆಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.',
    footer: 'ಶೈಕ್ಷಣಿಕ ಮಾದರಿ · ಅನಿರೀಕ್ಷಿತ ವಿನಂತಿಗಳನ್ನು ಸ್ವತಂತ್ರವಾಗಿ ಪರಿಶೀಲಿಸಿ.',
    lower: 'ಕಡಿಮೆ ಅಪಾಯ',
    caution: 'ಎಚ್ಚರಿಕೆ ಅಗತ್ಯ',
    high: 'ಹೆಚ್ಚಿನ ಅಪಾಯ',
    error: 'ಬ್ಯಾಕೆಂಡ್ ಸಂಪರ್ಕ ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. API ಸರ್ವರ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ ಪರಿಶೀಲಿಸಿ.',
    invalid: 'ವಿಶ್ಲೇಷಿಸಲು ಕನಿಷ್ಠ 3 ಅಕ್ಷರಗಳನ್ನು ನಮೂದಿಸಿ.',
    safeNote: 'ಕಡಿಮೆ ಸ್ಕೋರ್ ಬಂದರೆ ಸಂದೇಶ ಅಥವಾ ಲಿಂಕ್ ಸುರಕ್ಷಿತವೆಂದು ಖಚಿತವಾಗುವುದಿಲ್ಲ.',
    heuristic: 'ಇದು ನಿಯಮಾಧಾರಿತ ಅಪಾಯ ಸೂಚಕ ಮಾತ್ರ; ಖಚಿತ ವಂಚನೆ ಸಂಭವನೀಯತೆ ಅಥವಾ ಅಂತಿಮ ತೀರ್ಪಲ್ಲ.',
    otp: 'OTP ಅಥವಾ ಒನ್-ಟೈಮ್ ಪಾಸ್‌ವರ್ಡ್ ಉಲ್ಲೇಖಿಸಲಾಗಿದೆ',
    urgency: 'ತುರ್ತು ಅಥವಾ ಒತ್ತಡದ ಭಾಷೆ ಬಳಸಲಾಗಿದೆ',
    kyc: 'ಖಾತೆ ಅಥವಾ KYC ಪರಿಶೀಲನೆ ಕೇಳಲಾಗಿದೆ',
    prize: 'ಬಹುಮಾನ ಅಥವಾ ಉಡುಗೊರೆಯ ಭರವಸೆ ನೀಡಲಾಗಿದೆ',
    fee: 'ಮುಂಗಡ ಶುಲ್ಕ ಕೇಳಲಾಗಿದೆ',
    link: 'ವೆಬ್ ಲಿಂಕ್ ಇದೆ',
    noPattern: 'ನಿಗದಿಪಡಿಸಿದ ಎಚ್ಚರಿಕೆ ಮಾದರಿ ಪತ್ತೆಯಾಗಿಲ್ಲ',
    https: 'URL HTTPS ಬಳಸುತ್ತಿಲ್ಲ',
    hostname: 'ಹೋಸ್ಟ್‌ನೇಮ್ ಸ್ವರೂಪ ಅಸಾಮಾನ್ಯವಾಗಿದೆ',
    ip: 'ಡೊಮೇನ್ ಬದಲಿಗೆ IP ವಿಳಾಸ ಬಳಸಲಾಗಿದೆ',
    longHost: 'ಹೋಸ್ಟ್‌ನೇಮ್ ಅಸಾಮಾನ್ಯವಾಗಿ ಉದ್ದವಾಗಿದೆ',
    hyphens: 'ಹೋಸ್ಟ್‌ನೇಮ್‌ನಲ್ಲಿ ಹಲವು ಹೈಫನ್‌ಗಳಿವೆ',
    at: 'ಗಮ್ಯಸ್ಥಾನವನ್ನು ಮರೆಮಾಡಬಹುದಾದ @ ಚಿಹ್ನೆ ಇದೆ',
    keyword: 'ಸೂಕ್ಷ್ಮ ಖಾತೆ ಸಂಬಂಧಿತ ಪದವಿದೆ; ಇದೊಂದೇ ವಂಚನೆಯನ್ನು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ',
    noUrlPattern: 'ಮೂಲ URL ಎಚ್ಚರಿಕೆ ಸೂಚನೆ ಪತ್ತೆಯಾಗಿಲ್ಲ',
    advice: 'ಲಿಂಕ್‌ಗಳನ್ನು ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ ಅಥವಾ OTP, ಪಾಸ್‌ವರ್ಡ್ ಮತ್ತು ಪಾವತಿ ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಬೇಡಿ. ಅಧಿಕೃತ ಆ್ಯಪ್ ಅಥವಾ ಫೋನ್ ಸಂಖ್ಯೆಯ ಮೂಲಕ ಪರಿಶೀಲಿಸಿ.',
    safeAdvice: 'ಬಲವಾದ ಎಚ್ಚರಿಕೆ ಮಾದರಿ ಕಂಡುಬಂದಿಲ್ಲ. ಇದರಿಂದ ಸಂದೇಶ ಸುರಕ್ಷಿತವೆಂದು ಸಾಬೀತಾಗುವುದಿಲ್ಲ.',
    urlAdvice: 'ಅನುಮಾನಾಸ್ಪದ ಲಿಂಕ್‌ಗಳನ್ನು ತೆರೆಯಬೇಡಿ. ಡೊಮೇನ್ ಅನ್ನು ಸ್ವತಂತ್ರವಾಗಿ ಪರಿಶೀಲಿಸಿ.',
    urlHeuristic: 'URL ವಿಶ್ಲೇಷಣೆಯು ಸ್ಥಳೀಯ ನಿಯಮಗಳನ್ನು ಬಳಸುತ್ತದೆ; BSIS ಸಂದೇಶ ವರ್ಗೀಕರಣ ಮಾದರಿಯನ್ನು ಬಳಸುವುದಿಲ್ಲ.',
    historyMessage: 'ಸಂದೇಶ',
    historyConversation: 'ಸಂಭಾಷಣೆ',
    historyUrl: 'URL',
    language: 'ಭಾಷೆ',
  },
  hi: {
    prototype: 'प्रोटोटाइप डैशबोर्ड',
    eyebrow: 'AI आधारित धोखाधड़ी जागरूकता',
    headline: 'रुकें। जाँचें। सुरक्षित रहें।',
    subtitle: 'कोई कदम उठाने से पहले संदिग्ध संदेशों, बातचीत और लिंक की जाँच करें।',
    analysis: 'खतरे का विश्लेषण',
    check: 'संदेश या URL जाँचें',
    message: 'एक संदेश',
    conversation: 'पूरी बातचीत',
    url: 'URL',
    messageLabel: 'संदिग्ध संदेश यहाँ डालें',
    conversationLabel: 'पूरी बातचीत यहाँ डालें',
    urlLabel: 'संदिग्ध URL दर्ज करें — इसे न खोलें',
    messagePlaceholder: 'उदाहरण: आपका बैंक खाता बंद हो जाएगा। अपना KYC सत्यापित करें...',
    conversationPlaceholder: 'पूरी चैट या संदेशों की बातचीत यहाँ डालें...',
    urlPlaceholder: 'https://example.com/...',
    channel: 'संदेश का माध्यम',
    sms: 'SMS',
    email: 'ईमेल',
    chat: 'चैट',
    modeMessageHint: 'एक संदेश का अलग से विश्लेषण करें।',
    modeConversationHint: 'पूरी बातचीत का एक साथ विश्लेषण करें। माध्यम Chat पर सेट है।',
    modeUrlHint: 'URL की स्थानीय जाँच होगी। भेजे गए लिंक को खोला नहीं जाएगा।',
    privacy: 'OTP, पासवर्ड, PIN या बैंकिंग की गोपनीय जानकारी दर्ज न करें।',
    analyze: 'सुरक्षित रूप से जाँचें',
    analyzing: 'विश्लेषण हो रहा है...',
    assessment: 'मूल्यांकन',
    why: 'चेतावनी के कारण',
    recommendation: 'सुरक्षा सुझाव',
    model: 'पहचान मॉडल',
    modelUsed: 'BSIS मॉडल का उपयोग हुआ',
    modelSkipped: 'BSIS मॉडल का उपयोग नहीं हुआ',
    prediction: 'मॉडल का परिणाम',
    scam: 'धोखाधड़ी के रूप में चिह्नित',
    notFlagged: 'मॉडल ने चिह्नित नहीं किया',
    spam: 'स्पैम',
    ham: 'संभवतः सामान्य संदेश',
    classifierScore: 'कच्चा मॉडल स्कोर',
    threshold: 'निर्णय सीमा',
    classifierModel: 'वर्गीकरण मॉडल',
    legacyUsed: 'पुराने अंग्रेज़ी SMS मॉडल का भी उपयोग हुआ',
    legacySkipped: 'पुराने अंग्रेज़ी SMS मॉडल का उपयोग नहीं हुआ',
    legacyScore: 'पुराने मॉडल का स्पैम स्कोर',
    noModel: 'मॉडल का परिणाम उपलब्ध नहीं है',
    rawScoreNote: 'यह कच्चा मॉडल स्कोर है, प्रमाणित संभावना नहीं।',
    safety: 'सुरक्षा सबसे पहले',
    safetyText: 'OTP, पासवर्ड या PIN साझा न करें।',
    verify: 'स्वतंत्र रूप से सत्यापित करें',
    verifyText: 'आधिकारिक ऐप और ज्ञात संपर्क विवरणों का उपयोग करें।',
    recent: 'हाल की जाँच',
    refresh: 'रीफ़्रेश',
    empty: 'विश्लेषण के बाद आपकी हाल की जाँच यहाँ दिखाई देगी।',
    footer: 'शैक्षिक प्रोटोटाइप · अनपेक्षित अनुरोधों की स्वतंत्र रूप से जाँच करें।',
    lower: 'कम जोखिम',
    caution: 'सावधानी आवश्यक',
    high: 'उच्च जोखिम',
    error: 'बैकएंड से कनेक्शन नहीं हो पाया। जाँचें कि API सर्वर चल रहा है।',
    invalid: 'विश्लेषण के लिए कम से कम 3 अक्षर दर्ज करें।',
    safeNote: 'कम स्कोर का मतलब यह नहीं है कि संदेश या लिंक सुरक्षित है।',
    heuristic: 'यह अनुमान-आधारित जोखिम संकेतक है, प्रमाणित धोखाधड़ी संभावना या अंतिम निर्णय नहीं।',
    otp: 'OTP या वन-टाइम पासवर्ड का उल्लेख है',
    urgency: 'जल्दबाज़ी या दबाव वाली भाषा का उपयोग है',
    kyc: 'खाते या KYC सत्यापन की माँग है',
    prize: 'इनाम या उपहार का वादा किया गया है',
    fee: 'अग्रिम शुल्क माँगा गया है',
    link: 'वेब लिंक मौजूद है',
    noPattern: 'कोई निर्धारित चेतावनी पैटर्न नहीं मिला',
    https: 'URL HTTPS का उपयोग नहीं करता',
    hostname: 'होस्टनेम का प्रारूप असामान्य है',
    ip: 'डोमेन के बजाय सीधे IP पते का उपयोग है',
    longHost: 'होस्टनेम असामान्य रूप से लंबा है',
    hyphens: 'होस्टनेम में कई हाइफ़न हैं',
    at: 'इसमें @ चिह्न है जो गंतव्य को छिपा सकता है',
    keyword: 'संवेदनशील खाते से जुड़ा शब्द है; यह अकेले धोखाधड़ी साबित नहीं करता',
    noUrlPattern: 'URL का कोई बुनियादी चेतावनी संकेत नहीं मिला',
    advice: 'लिंक पर क्लिक न करें और OTP, पासवर्ड या भुगतान विवरण साझा न करें। आधिकारिक ऐप या फ़ोन नंबर से सत्यापित करें।',
    safeAdvice: 'कोई मज़बूत चेतावनी पैटर्न नहीं मिला। इससे संदेश सुरक्षित साबित नहीं होता।',
    urlAdvice: 'संदिग्ध लिंक न खोलें। डोमेन की स्वतंत्र रूप से जाँच करें और आधिकारिक वेबसाइट या ऐप का उपयोग करें।',
    urlHeuristic: 'URL विश्लेषण स्थानीय नियमों का उपयोग करता है, BSIS संदेश वर्गीकरण मॉडल का नहीं।',
    historyMessage: 'संदेश',
    historyConversation: 'बातचीत',
    historyUrl: 'URL',
    language: 'भाषा',
  },
}

type TranslationKey = keyof typeof translations.en

const signalKeys: Record<string, TranslationKey> = {
  'Mentions an OTP or one-time password': 'otp',
  'Uses urgency or pressure': 'urgency',
  'Requests account or KYC verification': 'kyc',
  'Promises a prize or reward': 'prize',
  'Requests an upfront fee': 'fee',
  'Contains a web link': 'link',
  'No configured warning pattern was detected': 'noPattern',
  'URL does not use HTTPS': 'https',
  'Hostname format looks unusual': 'hostname',
  'Uses a raw IP address instead of a domain': 'ip',
  'Unusually long hostname': 'longHost',
  'Hostname contains several hyphens': 'hyphens',
  'Contains an @ symbol that may obscure the destination': 'at',
  'Contains a sensitive-account keyword; this alone does not prove fraud': 'keyword',
  'No basic URL warning signal was detected': 'noUrlPattern',
}

export default function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [mode, setMode] = useState<Mode>('message')
  const [channel, setChannel] = useState<Channel>('sms')
  const [value, setValue] = useState('')
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<HistoryItem[]>([])

  const t = translations[language]

  useEffect(() => {
    void refresh()
  }, [])

  async function refresh() {
    try {
      const response = await fetch(`${API}/api/history`)
      if (response.ok) {
        const data = await response.json()
        setHistory(data.items ?? [])
      }
    } catch {
      // History is optional; analysis can still work.
    }
  }

  function changeMode(nextMode: Mode) {
    setMode(nextMode)
    setResult(null)
    setError('')
  }

  async function analyze() {
    if (value.trim().length < 3) {
      setError(t.invalid)
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    const isUrl = mode === 'url'
    const inputMode = mode === 'conversation' ? 'conversation' : 'single_message'
    const selectedChannel = mode === 'conversation' ? 'chat' : channel

    try {
      const response = await fetch(
        `${API}${isUrl ? '/api/analyze-url' : '/api/analyze'}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(
            isUrl
              ? { url: value.trim() }
              : {
                  text: value.trim(),
                  channel: selectedChannel,
                  input_mode: inputMode,
                },
          ),
        },
      )

      if (!response.ok) throw new Error(`API returned ${response.status}`)

      const data: Result = await response.json()
      setResult(data)
      await refresh()
    } catch {
      setError(t.error)
    } finally {
      setLoading(false)
    }
  }

  function translatedSignal(signal: string) {
    const key = signalKeys[signal]
    return key ? t[key] : signal
  }

  function translatedCategory(category: string) {
    if (category === 'High risk') return t.high
    if (category === 'Needs caution') return t.caution
    return t.lower
  }

  function translatedPrediction(prediction: string) {
    if (prediction === 'scam') return t.scam
    if (prediction === 'not_flagged') return t.notFlagged
    if (prediction === 'spam') return t.spam
    if (prediction === 'ham') return t.ham
    return prediction
  }

  function translatedRecommendation() {
    if (!result) return ''
    if (mode === 'url') return t.urlAdvice
    return result.risk_score >= 30 ? t.advice : t.safeAdvice
  }

  function translatedHistoryType(type: string) {
    if (type === 'url') return t.historyUrl
    if (type === 'conversation') return t.historyConversation
    return t.historyMessage
  }

  function percent(value?: number | null) {
    if (value === undefined || value === null || Number.isNaN(value)) return '—'
    return `${(value * 100).toFixed(1)}%`
  }

  const fieldLabel = mode === 'url'
    ? t.urlLabel
    : mode === 'conversation'
      ? t.conversationLabel
      : t.messageLabel

  const placeholder = mode === 'url'
    ? t.urlPlaceholder
    : mode === 'conversation'
      ? t.conversationPlaceholder
      : t.messagePlaceholder

  const modeHint = mode === 'url'
    ? t.modeUrlHint
    : mode === 'conversation'
      ? t.modeConversationHint
      : t.modeMessageHint

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="logo"><ShieldCheck size={25} /></div>
          <div>
            <b>CyberSahay</b>
            <small>CYBER SAFETY INTELLIGENCE</small>
          </div>
        </div>

        <div className="top-actions">
          <label className="language-control">
            <Languages size={16} />
            <span>{t.language}</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value as Language)}
              aria-label={t.language}
            >
              <option value="en">English</option>
              <option value="kn">ಕನ್ನಡ</option>
              <option value="hi">हिन्दी</option>
            </select>
          </label>
          <span className="status"><span className="status-dot" />{t.prototype}</span>
        </div>
      </header>

      <section className="hero">
        <small>{t.eyebrow}</small>
        <h1>
          {language === 'en' ? (
            <>Pause. Check. <em>Stay safe.</em></>
          ) : t.headline}
        </h1>
        <p>{t.subtitle}</p>
      </section>

      <section className="layout">
        <div className="panel analyzer-panel">
          <div className="heading">
            <div>
              <small>{t.analysis}</small>
              <h2>{t.check}</h2>
            </div>
            <Activity size={22} />
          </div>

          <div className="tabs">
            <button
              className={mode === 'message' ? 'active' : ''}
              onClick={() => changeMode('message')}
              type="button"
            >
              <MessageSquareWarning size={16} /> {t.message}
            </button>
            <button
              className={mode === 'conversation' ? 'active' : ''}
              onClick={() => changeMode('conversation')}
              type="button"
            >
              <MessagesSquare size={16} /> {t.conversation}
            </button>
            <button
              className={mode === 'url' ? 'active' : ''}
              onClick={() => changeMode('url')}
              type="button"
            >
              <Link2 size={16} /> {t.url}
            </button>
          </div>

          {mode === 'message' && (
            <label className="channel-control">
              <span>{t.channel}</span>
              <select
                value={channel}
                onChange={(event) => setChannel(event.target.value as Channel)}
              >
                <option value="sms">{t.sms}</option>
                <option value="email">{t.email}</option>
                <option value="chat">{t.chat}</option>
              </select>
            </label>
          )}

          <p className="mode-hint">{modeHint}</p>

          <label className="field-label">{fieldLabel}</label>
          <textarea
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={placeholder}
            aria-label={fieldLabel}
          />

          <p className="privacy">
            <ShieldCheck size={15} /> {t.privacy}
          </p>

          <button
            className="analyze"
            disabled={loading || value.trim().length < 3}
            onClick={analyze}
            type="button"
          >
            <Search size={17} />
            {loading ? t.analyzing : t.analyze}
          </button>

          {error && <p className="error" role="alert">{error}</p>}

          {result && (
            <section className="result" aria-live="polite">
              <div className="resulttop">
                <div>
                  <small>{t.assessment}</small>
                  <h3>{translatedCategory(result.category)}</h3>
                </div>
                <strong>{result.risk_score}<small>/100</small></strong>
              </div>

              <div className="meter">
                <span
                  className={
                    result.risk_score >= 65
                      ? 'meter-high'
                      : result.risk_score >= 30
                        ? 'meter-medium'
                        : 'meter-low'
                  }
                  style={{ width: `${Math.max(0, Math.min(100, result.risk_score))}%` }}
                />
              </div>

              <p className="risk-note">{t.safeNote}</p>

              <div className="result-section">
                <b>{t.why}</b>
                <ul>
                  {result.explanation.map((signal, index) => (
                    <li key={`${signal}-${index}`}>{translatedSignal(signal)}</li>
                  ))}
                </ul>
              </div>


<div className="model-info">
  <div className="model-heading">
    <Activity size={16} />
    <b>{t.model}</b>
  </div>

  {mode === 'url' ? (
    <p>{t.urlHeuristic}</p>
  ) : (
    <>
      {result.model_used !== undefined && (
        <p>{result.model_used ? t.modelUsed : t.modelSkipped}</p>
      )}

      {result.model_prediction && (
        <p>
          {t.prediction}:{' '}
          <strong>{translatedPrediction(result.model_prediction)}</strong>
        </p>
      )}

      {result.classifier_model && (
        <p>{t.classifierModel}: <strong>{result.classifier_model}</strong></p>
      )}

      {result.classifier_score != null && (
        <div className="model-metrics">
          <p>{t.classifierScore}: <strong>{percent(result.classifier_score)}</strong></p>
          {result.classifier_threshold != null && (
            <p>{t.threshold}: <strong>{percent(result.classifier_threshold)}</strong></p>
          )}
          <small>{t.rawScoreNote}</small>
        </div>
      )}

      {result.legacy_model_used !== undefined && (
        <p>{result.legacy_model_used ? t.legacyUsed : t.legacySkipped}</p>
      )}

      {result.legacy_model_used === true && result.legacy_spam_score != null && (
        <p>{t.legacyScore}: <strong>{percent(result.legacy_spam_score)}</strong></p>
      )}

      {!result.model_used && !result.model_prediction && result.classifier_score == null && (
        <p>{t.noModel}</p>
      )}
    </>
  )}
</div>


              <div className="advice">
                <AlertTriangle size={18} />
                <div>
                  <b>{t.recommendation}</b>
                  <p>{translatedRecommendation()}</p>
                </div>
              </div>

              <small className="note">{t.heuristic}</small>
            </section>
          )}
        </div>

        <aside>
          <div className="tip">
            <ShieldCheck />
            <div>
              <b>{t.safety}</b>
              <p>{t.safetyText}</p>
            </div>
          </div>

          <div className="tip">
            <Link2 />
            <div>
              <b>{t.verify}</b>
              <p>{t.verifyText}</p>
            </div>
          </div>

          <div className="panel hist">
            <div className="heading">
              <h2><History size={17} /> {t.recent}</h2>
              <button className="refresh" onClick={() => void refresh()} type="button">
                <RefreshCw size={13} /> {t.refresh}
              </button>
            </div>

            {history.length === 0 ? (
              <p className="muted">{t.empty}</p>
            ) : (
              history.slice(0, 6).map((item) => (
                <div className="histrow" key={item.id}>
                  <span>{translatedHistoryType(item.input_type)}</span>
                  <b>{translatedCategory(item.category)}</b>
                  <small>{item.risk_score}/100</small>
                </div>
              ))
            )}
          </div>

          <div className="disclaimer">
            <Info size={16} />
            <p>{t.heuristic}</p>
          </div>
        </aside>
      </section>

      <footer>
        CyberSahay · {t.footer}
      </footer>
    </main>
  )
}
