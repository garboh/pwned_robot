"""
UI strings for Pwned Robot — Italian and English.

Usage:
    from strings import t, SUBSCRIPTION_PRICE_STARS
    text = t("welcome", lang="it", name=" Francesco", badge="⭐")
"""

from typing import Any

# Annual Premium price in Telegram Stars
SUBSCRIPTION_PRICE_STARS = 500

SUPPORTED_LANGUAGES = ("it", "en")

STRINGS: dict[str, dict[str, str]] = {
    # ================================================================== #
    #  ITALIANO                                                            #
    # ================================================================== #
    "it": {
        # --- Buttons ---
        "btn_check":        "🔍 Controlla Email",
        "btn_stats":        "📊 Statistiche",
        "btn_premium":      "⭐ Premium",
        "btn_help":         "❓ Aiuto",
        "btn_channel":      "📢 Canale Notizie Violazioni",
        "btn_buy":          "⭐ Abbonati con Stars",
        "btn_open_channel": "📢 Apri il Canale",
        "btn_lang_it":      "🇮🇹 Italiano ✓",
        "btn_lang_en":      "🇬🇧 English",

        # --- Welcome ---
        "welcome": (
            "🔐 <b>Benvenuto{name} in Pwned Robot!</b> {badge}\n\n"
            "Controllo se i tuoi account sono stati compromessi in violazioni "
            "di dati pubbliche usando il database di "
            "<a href='https://haveibeenpwned.com'>Have I Been Pwned</a>.\n\n"
            "<b>Comandi disponibili:</b>\n"
            "📧 /check — Controlla un'email\n"
            "📊 /stats — Le tue statistiche\n"
            "🔔 /monitor — Monitoraggio giornaliero <b>(Premium)</b>\n"
            "📢 /updates — Notizie sulle nuove violazioni\n"
            "⭐ /subscribe — Abbonamento Premium\n"
            "🌐 /language — Cambia lingua\n"
            "ℹ️ /help — Aiuto\n\n"
            "🔒 <i>Non memorizziamo le tue email in chiaro.</i>"
        ),

        # --- Help ---
        "help": (
            "<b>📚 Guida di Pwned Robot</b>\n\n"
            "<b>📧 /check</b>\n"
            "Controlla se un'email è stata compromessa.\n"
            "Uso: <code>/check email@example.com</code>\n\n"
            "<b>📊 /stats</b>\n"
            "Le tue statistiche di controllo personali.\n\n"
            "<b>🔔 /monitor</b> <i>(Premium)</i>\n"
            "Aggiungi un'email al monitoraggio giornaliero automatico.\n"
            "Uso: <code>/monitor email@example.com</code>\n\n"
            "<b>🗑️ /unmonitor</b> <i>(Premium)</i>\n"
            "Rimuovi un'email dal monitoraggio.\n\n"
            "<b>📋 /mymonitors</b> <i>(Premium)</i>\n"
            "Visualizza le email monitorate attualmente.\n\n"
            "<b>📢 /updates</b>\n"
            "Apri il canale con notizie in tempo reale sulle nuove violazioni.\n\n"
            "<b>⭐ /subscribe</b>\n"
            "Scopri i vantaggi del piano Premium.\n\n"
            "<b>🌐 /language</b>\n"
            "Cambia la lingua del bot.\n\n"
            "<b>🔐 /privacy</b>\n"
            "Leggi la nostra politica sulla privacy.\n\n"
            "<b>🆘 Cosa fare se trovi una violazione?</b>\n"
            "✓ Cambia la password immediatamente\n"
            "✓ Abilita l'autenticazione a due fattori (2FA)\n"
            "✓ Controlla eventuali attività sospette\n"
            "✓ Usa password uniche per ogni servizio\n\n"
            "📢 Segui <a href='https://t.me/HIBP_updates'>@HIBP_updates</a> per ricevere "
            "notifiche su ogni nuova violazione scoperta!"
        ),

        # --- Privacy ---
        "privacy": (
            "🔐 <b>Politica sulla Privacy</b>\n\n"
            "<b>Cosa raccogliamo:</b>\n"
            "• ID Telegram, username e nome\n"
            "• Storico dei controlli email (cifrato)\n"
            "• Preferenze e impostazioni\n\n"
            "<b>Come usiamo i dati:</b>\n"
            "• Per fornire il servizio di controllo violazioni\n"
            "• Per il monitoraggio giornaliero (Premium)\n"
            "• Per statistiche aggregate anonime\n\n"
            "<b>Cosa NON facciamo:</b>\n"
            "• Non vendiamo i tuoi dati a terze parti\n"
            "• Non memorizziamo le email in chiaro\n"
            "• Non condividiamo informazioni personali\n\n"
            "<b>Sicurezza:</b>\n"
            "• Le email vengono hashate (SHA-256) prima della memorizzazione\n"
            "• Connessioni cifrate con l'API HIBP\n"
            "• Audit log di tutte le operazioni sensibili\n\n"
            "<b>I tuoi diritti:</b>\n"
            "Puoi richiedere la cancellazione dei tuoi dati contattando "
            "un amministratore del bot.\n\n"
            "<i>Dati forniti da "
            "<a href='https://haveibeenpwned.com'>HaveIBeenPwned.com</a></i>"
        ),

        # --- Language ---
        "language_select":    "🌐 <b>Seleziona la lingua / Select language:</b>",
        "language_changed_it": "✅ Lingua impostata su <b>Italiano</b>.",
        "language_changed_en": "✅ Language set to <b>English</b>.",

        # --- Check ---
        "check_ask_email": (
            "📧 <b>Inserisci l'email da controllare:</b>\n\n"
            "Esempio: <code>example@email.com</code>"
        ),
        "check_invalid_email": (
            "❌ <b>Email non valida!</b>\n\n"
            "Inserisci un'email valida: <code>email@example.com</code>"
        ),
        "check_injection":   "❌ <b>Richiesta non valida!</b>",
        "check_processing":  "🔍 <b>Sto controllando {email}...</b>\n\nAttendi qualche secondo.",
        "check_no_breach": (
            "✅ <b>Buone notizie!</b>\n\n"
            "L'email <code>{email}</code> non è stata trovata "
            "in alcuna violazione di dati pubblica.\n\n"
            "<i>Nota: questo non garantisce sicurezza assoluta, "
            "ma nessuna violazione pubblica conosciuta include questa email.</i>"
        ),
        "check_breach_header":        "⚠️ <b>ATTENZIONE! Email compromessa!</b>\n\nEmail: <code>{email}</code>\n\n",
        "check_breach_count":         "🔓 <b>Violazioni trovate: {count}</b>\n",
        "check_breach_item":          "• <b>{name}</b> — {date}\n",
        "check_breach_item_premium":  "• <b>{name}</b> — {date}\n  Account coinvolti: {count}\n  Dati esposti: {classes}\n",
        "check_more_breaches":        "• … e altre <b>{n}</b> violazioni.\n⭐ Abbonati per vederle tutte! /subscribe\n",
        "check_pastes_count":         "📋 <b>Paste trovate: {count}</b>\n",
        "check_pastes_detail":        "• {source} — {title}\n",
        "check_pastes_hint":          "Controlla haveibeenpwned.com per i dettagli.\n",
        "check_actions": (
            "\n<b>🛡️ Azioni consigliate:</b>\n"
            "1️⃣ Cambia la password immediatamente\n"
            "2️⃣ Abilita l'autenticazione a due fattori (2FA)\n"
            "3️⃣ Monitora il tuo account per attività sospette\n"
            "4️⃣ Verifica gli altri tuoi account\n"
        ),
        "check_monitor_hint": "\n🔔 Usa /monitor per ricevere notifiche automatiche su questa email ogni giorno.",
        "check_api_error": (
            "❌ <b>Errore durante il controllo</b>\n\n"
            "L'API di Have I Been Pwned è temporaneamente non disponibile.\n"
            "Riprova tra qualche minuto."
        ),
        "check_generic_error": "❌ Si è verificato un errore inaspettato. Riprova.",

        # --- Rate limit ---
        "rate_limit":      "⚠️ <b>Limite di richieste raggiunto</b>\n\nAttendi qualche secondo prima di riprovare.",
        "rate_limit_hint": "\n💡 Abbonati a Premium per limiti più alti! /subscribe",

        # --- Stats ---
        "stats_header":        "📊 <b>Le tue statistiche</b>\n\n",
        "stats_premium_line":  "\n⭐ <b>Premium</b> dal {since}\n🔔 Email monitorate: {monitored}/{max}\n",
        "stats_checks":        "📧 Controlli totali: {total}\n",
        "stats_breaches":      "🔓 Violazioni trovate: {total}\n",
        "stats_avg":           "📈 Media violazioni/check: {avg:.2f}\n",
        "stats_recent":        "\n<b>Ultimi 5 controlli:</b>\n",
        "stats_recent_item":   "{icon} {date}{breach_info}\n",
        "stats_subscribe_hint": "\n⭐ <i>Abbonati a Premium per il monitoraggio automatico! /subscribe</i>",

        # --- Subscribe ---
        "subscribe_already": (
            "⭐ <b>Sei già un utente Premium!</b>\n\n"
            "<b>I tuoi vantaggi attivi:</b>\n"
            "🔔 Monitoraggio giornaliero fino a {max} email\n"
            "📋 Dettagli completi di tutte le violazioni\n"
            "📊 Dati esposti per ogni violazione\n"
            "⚡ Limite aumentato (30 richieste/minuto)\n"
            "🚨 Notifiche automatiche su nuove violazioni\n\n"
            "Usa /monitor per aggiungere un'email al monitoraggio."
        ),
        "subscribe_info": (
            "⭐ <b>Pwned Robot Premium</b>\n\n"
            "<b>Cosa ottieni con il Premium:</b>\n"
            "🔔 Monitoraggio giornaliero automatico fino a {max} email\n"
            "📋 Dettagli completi su tutte le violazioni trovate\n"
            "📊 Categorie di dati esposti per ogni breach\n"
            "⚡ Limite di richieste aumentato (30/min vs 5)\n"
            "🚨 Notifiche Telegram istantanee per nuove violazioni\n"
            "📋 Dettagli delle paste trovate\n\n"
            "💰 <b>Abbonamento annuale: {price} ⭐ Telegram Stars</b>\n\n"
            "📢 Rimani aggiornato seguendo:\n"
            "👉 <a href='https://t.me/HIBP_updates'>@HIBP_updates</a>"
        ),

        # --- Invoice ---
        "invoice_title":       "Pwned Robot Premium — Annuale",
        "invoice_description": (
            "Accesso Premium per 1 anno: monitoraggio giornaliero di 5 email, "
            "dettagli completi delle violazioni, limite di richieste aumentato."
        ),
        "invoice_label":   "Premium Annuale",
        "payment_success": (
            "🎉 <b>Pagamento ricevuto! Benvenuto nel Premium!</b>\n\n"
            "Il tuo abbonamento è ora attivo.\n"
            "Usa /monitor per iniziare a monitorare le tue email."
        ),
        "payment_error": "❌ Errore durante l'attivazione. Contatta un amministratore.",

        # --- Updates ---
        "updates": (
            "📢 <b>Notizie in tempo reale sulle violazioni di dati</b>\n\n"
            "Unisciti al canale per essere avvisato ogni volta che "
            "viene scoperta una nuova violazione:\n\n"
            "👉 <a href='https://t.me/HIBP_updates'>t.me/HIBP_updates</a>\n\n"
            "Riceverai notifiche su:\n"
            "• Nuove violazioni aggiunte a HIBP\n"
            "• Aggiornamenti su violazioni già note\n"
            "• Consigli su come proteggere i tuoi account"
        ),

        # --- Monitor ---
        "monitor_premium_required": (
            "⭐ <b>Funzionalità Premium</b>\n\n"
            "Il monitoraggio giornaliero è riservato agli abbonati Premium.\n"
            "Usa /subscribe per scoprire i vantaggi e abbonarti."
        ),
        "monitor_usage": (
            "🔔 <b>Monitoraggio giornaliero email</b>\n\n"
            "Puoi monitorare fino a <b>{max} email</b>.\n"
            "Ogni giorno alle 8:00 UTC controllerò automaticamente le violazioni "
            "e ti avviserò se vengono rilevate novità.\n\n"
            "Uso: <code>/monitor email@example.com</code>\n\n"
            "Usa /mymonitors per vedere le email già monitorate."
        ),
        "monitor_invalid_email":  "❌ <b>Email non valida.</b>\nEsempio: <code>/monitor email@example.com</code>",
        "monitor_limit_reached": (
            "⚠️ Hai già raggiunto il limite di <b>{max} email</b> monitorate.\n"
            "Rimuovi un'email con /unmonitor prima di aggiungerne un'altra."
        ),
        "monitor_processing": "🔍 Controllo iniziale di <code>{email}</code>...",
        "monitor_added": (
            "✅ <b>Email aggiunta al monitoraggio!</b>\n\n"
            "📧 <code>{email}</code>\n"
            "🔓 Violazioni attuali: {breaches}\n"
            "📋 Paste attuali: {pastes}\n\n"
            "Ti avviserò ogni giorno (8:00 UTC) se vengono rilevate nuove violazioni.\n\n"
            "Slot utilizzati: {used}/{max}"
        ),
        "monitor_already": "ℹ️ L'email <code>{email}</code> è già in monitoraggio.",

        # --- Unmonitor ---
        "unmonitor_usage":     "Uso: <code>/unmonitor email@example.com</code>\n\nUsa /mymonitors per vedere le email monitorate.",
        "unmonitor_removed":   "✅ <code>{email}</code> rimossa dal monitoraggio.",
        "unmonitor_not_found": "ℹ️ <code>{email}</code> non era in monitoraggio.",

        # --- My Monitors ---
        "mymonitors_none": (
            "🔔 <b>Nessuna email in monitoraggio.</b>\n\n"
            "Aggiungi un'email con:\n<code>/monitor email@example.com</code>"
        ),
        "mymonitors_header": "🔔 <b>Email monitorate ({count}/{max}):</b>\n\n",
        "mymonitors_item": (
            "• <code>{email}</code>\n"
            "  Violazioni: {breaches} | Paste: {pastes} | Ultimo check: {last}\n\n"
        ),
        "mymonitors_hint": "Rimuovi con <code>/unmonitor email@example.com</code>",

        # --- Cancel / Errors ---
        "cancel":         "❌ Operazione annullata.",
        "user_not_found": "❌ Errore: utente non trovato.",

        # --- Scheduler notifications ---
        "alert_header":      "🚨 <b>NUOVA VIOLAZIONE RILEVATA!</b>\n\n📧 Email: <code>{email}</code>\n\n",
        "alert_breaches":    "🔓 <b>+{count} nuova/e violazione/i:</b>\n",
        "alert_breach_item": "• <b>{name}</b> ({date})\n  Account coinvolti: {records}\n",
        "alert_pastes":      "📋 <b>+{count} nuovo/i paste rilevato/i</b>\n\n",
        "alert_actions": (
            "<b>🛡️ Azioni consigliate:</b>\n"
            "1️⃣ Cambia la password immediatamente\n"
            "2️⃣ Abilita l'autenticazione a due fattori (2FA)\n"
            "3️⃣ Monitora attività sospette sul tuo account\n\n"
            "Usa /check per vedere tutte le violazioni nel dettaglio.\n\n"
            "📢 Rimani aggiornato su <a href='https://t.me/HIBP_updates'>@HIBP_updates</a>"
        ),
    },

    # ================================================================== #
    #  ENGLISH                                                             #
    # ================================================================== #
    "en": {
        # --- Buttons ---
        "btn_check":        "🔍 Check Email",
        "btn_stats":        "📊 Statistics",
        "btn_premium":      "⭐ Premium",
        "btn_help":         "❓ Help",
        "btn_channel":      "📢 Breach News Channel",
        "btn_buy":          "⭐ Subscribe with Stars",
        "btn_open_channel": "📢 Open Channel",
        "btn_lang_it":      "🇮🇹 Italiano",
        "btn_lang_en":      "🇬🇧 English ✓",

        # --- Welcome ---
        "welcome": (
            "🔐 <b>Welcome{name} to Pwned Robot!</b> {badge}\n\n"
            "I check whether your accounts were exposed in known data breaches, "
            "using the <a href='https://haveibeenpwned.com'>Have I Been Pwned</a> database.\n\n"
            "<b>Available commands:</b>\n"
            "📧 /check — Check an email\n"
            "📊 /stats — Your statistics\n"
            "🔔 /monitor — Daily monitoring <b>(Premium)</b>\n"
            "📢 /updates — Breach news\n"
            "⭐ /subscribe — Premium subscription\n"
            "🌐 /language — Change language\n"
            "ℹ️ /help — Help\n\n"
            "🔒 <i>We never store your emails in plaintext.</i>"
        ),

        # --- Help ---
        "help": (
            "<b>📚 Pwned Robot Guide</b>\n\n"
            "<b>📧 /check</b>\n"
            "Check if an email was found in a data breach.\n"
            "Usage: <code>/check email@example.com</code>\n\n"
            "<b>📊 /stats</b>\n"
            "Your personal check history and statistics.\n\n"
            "<b>🔔 /monitor</b> <i>(Premium)</i>\n"
            "Add an email to daily automatic monitoring.\n"
            "Usage: <code>/monitor email@example.com</code>\n\n"
            "<b>🗑️ /unmonitor</b> <i>(Premium)</i>\n"
            "Remove an email from monitoring.\n\n"
            "<b>📋 /mymonitors</b> <i>(Premium)</i>\n"
            "List all currently monitored emails.\n\n"
            "<b>📢 /updates</b>\n"
            "Open the real-time breach news channel.\n\n"
            "<b>⭐ /subscribe</b>\n"
            "Discover Premium plan benefits.\n\n"
            "<b>🌐 /language</b>\n"
            "Change the bot language.\n\n"
            "<b>🔐 /privacy</b>\n"
            "Read our privacy policy.\n\n"
            "<b>🆘 What to do when a breach is found?</b>\n"
            "✓ Change your password immediately\n"
            "✓ Enable two-factor authentication (2FA)\n"
            "✓ Monitor your account for suspicious activity\n"
            "✓ Use unique passwords for every service\n\n"
            "📢 Follow <a href='https://t.me/HIBP_updates'>@HIBP_updates</a> to be notified "
            "whenever a new breach is discovered!"
        ),

        # --- Privacy ---
        "privacy": (
            "🔐 <b>Privacy Policy</b>\n\n"
            "<b>What we collect:</b>\n"
            "• Telegram ID, username and name\n"
            "• Check history (hashed emails)\n"
            "• Preferences and settings\n\n"
            "<b>How we use data:</b>\n"
            "• To provide the breach checking service\n"
            "• For daily monitoring (Premium users)\n"
            "• For anonymous aggregate statistics\n\n"
            "<b>What we do NOT do:</b>\n"
            "• We do not sell your data to third parties\n"
            "• We do not store emails in plaintext\n"
            "• We do not share personal information\n\n"
            "<b>Security:</b>\n"
            "• Emails are SHA-256 hashed before storage\n"
            "• Encrypted connections to the HIBP API\n"
            "• Audit log for all sensitive operations\n\n"
            "<b>Your rights:</b>\n"
            "You can request data deletion by contacting a bot administrator.\n\n"
            "<i>Data provided by "
            "<a href='https://haveibeenpwned.com'>HaveIBeenPwned.com</a></i>"
        ),

        # --- Language ---
        "language_select":    "🌐 <b>Seleziona la lingua / Select language:</b>",
        "language_changed_it": "✅ Lingua impostata su <b>Italiano</b>.",
        "language_changed_en": "✅ Language set to <b>English</b>.",

        # --- Check ---
        "check_ask_email": (
            "📧 <b>Enter the email to check:</b>\n\n"
            "Example: <code>example@email.com</code>"
        ),
        "check_invalid_email": (
            "❌ <b>Invalid email!</b>\n\n"
            "Please enter a valid email: <code>email@example.com</code>"
        ),
        "check_injection":   "❌ <b>Invalid request!</b>",
        "check_processing":  "🔍 <b>Checking {email}...</b>\n\nPlease wait a few seconds.",
        "check_no_breach": (
            "✅ <b>Good news!</b>\n\n"
            "The email <code>{email}</code> was not found "
            "in any known public data breach.\n\n"
            "<i>Note: this does not guarantee complete security, "
            "but no known public breach includes this email.</i>"
        ),
        "check_breach_header":        "⚠️ <b>WARNING! Email compromised!</b>\n\nEmail: <code>{email}</code>\n\n",
        "check_breach_count":         "🔓 <b>Breaches found: {count}</b>\n",
        "check_breach_item":          "• <b>{name}</b> — {date}\n",
        "check_breach_item_premium":  "• <b>{name}</b> — {date}\n  Affected accounts: {count}\n  Exposed data: {classes}\n",
        "check_more_breaches":        "• … and <b>{n}</b> more breaches.\n⭐ Subscribe to see all! /subscribe\n",
        "check_pastes_count":         "📋 <b>Pastes found: {count}</b>\n",
        "check_pastes_detail":        "• {source} — {title}\n",
        "check_pastes_hint":          "Check haveibeenpwned.com for details.\n",
        "check_actions": (
            "\n<b>🛡️ Recommended actions:</b>\n"
            "1️⃣ Change your password immediately\n"
            "2️⃣ Enable two-factor authentication (2FA)\n"
            "3️⃣ Monitor your account for suspicious activity\n"
            "4️⃣ Check your other accounts\n"
        ),
        "check_monitor_hint": "\n🔔 Use /monitor to receive daily automatic alerts for this email.",
        "check_api_error": (
            "❌ <b>Check failed</b>\n\n"
            "The Have I Been Pwned API is temporarily unavailable.\n"
            "Please try again in a few minutes."
        ),
        "check_generic_error": "❌ An unexpected error occurred. Please try again.",

        # --- Rate limit ---
        "rate_limit":      "⚠️ <b>Rate limit reached</b>\n\nPlease wait a few seconds before retrying.",
        "rate_limit_hint": "\n💡 Subscribe to Premium for higher limits! /subscribe",

        # --- Stats ---
        "stats_header":         "📊 <b>Your statistics</b>\n\n",
        "stats_premium_line":   "\n⭐ <b>Premium</b> since {since}\n🔔 Monitored emails: {monitored}/{max}\n",
        "stats_checks":         "📧 Total checks: {total}\n",
        "stats_breaches":       "🔓 Breaches found: {total}\n",
        "stats_avg":            "📈 Average breaches/check: {avg:.2f}\n",
        "stats_recent":         "\n<b>Last 5 checks:</b>\n",
        "stats_recent_item":    "{icon} {date}{breach_info}\n",
        "stats_subscribe_hint": "\n⭐ <i>Subscribe to Premium for daily automatic monitoring! /subscribe</i>",

        # --- Subscribe ---
        "subscribe_already": (
            "⭐ <b>You are already a Premium user!</b>\n\n"
            "<b>Your active benefits:</b>\n"
            "🔔 Daily monitoring for up to {max} emails\n"
            "📋 Full breach details (unlimited)\n"
            "📊 Exposed data categories per breach\n"
            "⚡ Higher rate limit (30 req/min)\n"
            "🚨 Automatic Telegram alerts on new breaches\n\n"
            "Use /monitor to add an email to monitoring."
        ),
        "subscribe_info": (
            "⭐ <b>Pwned Robot Premium</b>\n\n"
            "<b>What you get with Premium:</b>\n"
            "🔔 Daily automatic monitoring for up to {max} emails\n"
            "📋 Full breach list with all details\n"
            "📊 Exposed data categories per breach\n"
            "⚡ Higher rate limit (30 req/min vs 5)\n"
            "🚨 Instant Telegram alerts on new breaches\n"
            "📋 Paste source details\n\n"
            "💰 <b>Annual subscription: {price} ⭐ Telegram Stars</b>\n\n"
            "📢 Stay informed:\n"
            "👉 <a href='https://t.me/HIBP_updates'>@HIBP_updates</a>"
        ),

        # --- Invoice ---
        "invoice_title":       "Pwned Robot Premium — Annual",
        "invoice_description": (
            "Premium access for 1 year: daily monitoring for 5 emails, "
            "full breach details, higher rate limits."
        ),
        "invoice_label":   "Annual Premium",
        "payment_success": (
            "🎉 <b>Payment received! Welcome to Premium!</b>\n\n"
            "Your subscription is now active.\n"
            "Use /monitor to start monitoring your emails."
        ),
        "payment_error": "❌ Activation error. Please contact an administrator.",

        # --- Updates ---
        "updates": (
            "📢 <b>Real-time breach news</b>\n\n"
            "Join the channel to be notified every time "
            "a new breach is discovered:\n\n"
            "👉 <a href='https://t.me/HIBP_updates'>t.me/HIBP_updates</a>\n\n"
            "You'll receive notifications about:\n"
            "• New breaches added to HIBP\n"
            "• Updates on known breaches\n"
            "• Tips to protect your accounts"
        ),

        # --- Monitor ---
        "monitor_premium_required": (
            "⭐ <b>Premium feature</b>\n\n"
            "Daily email monitoring is reserved for Premium subscribers.\n"
            "Use /subscribe to learn about the benefits and subscribe."
        ),
        "monitor_usage": (
            "🔔 <b>Daily email monitoring</b>\n\n"
            "You can monitor up to <b>{max} emails</b>.\n"
            "Every day at 8:00 UTC I will automatically check for new breaches "
            "and notify you if anything new is found.\n\n"
            "Usage: <code>/monitor email@example.com</code>\n\n"
            "Use /mymonitors to see your monitored emails."
        ),
        "monitor_invalid_email":  "❌ <b>Invalid email.</b>\nExample: <code>/monitor email@example.com</code>",
        "monitor_limit_reached": (
            "⚠️ You have reached the limit of <b>{max} monitored emails</b>.\n"
            "Remove one with /unmonitor before adding another."
        ),
        "monitor_processing": "🔍 Running initial check for <code>{email}</code>...",
        "monitor_added": (
            "✅ <b>Email added to monitoring!</b>\n\n"
            "📧 <code>{email}</code>\n"
            "🔓 Current breaches: {breaches}\n"
            "📋 Current pastes: {pastes}\n\n"
            "I will notify you daily (8:00 UTC) if new breaches are detected.\n\n"
            "Slots used: {used}/{max}"
        ),
        "monitor_already": "ℹ️ <code>{email}</code> is already being monitored.",

        # --- Unmonitor ---
        "unmonitor_usage":     "Usage: <code>/unmonitor email@example.com</code>\n\nUse /mymonitors to list monitored emails.",
        "unmonitor_removed":   "✅ <code>{email}</code> removed from monitoring.",
        "unmonitor_not_found": "ℹ️ <code>{email}</code> was not being monitored.",

        # --- My Monitors ---
        "mymonitors_none": (
            "🔔 <b>No emails being monitored.</b>\n\n"
            "Add one with:\n<code>/monitor email@example.com</code>"
        ),
        "mymonitors_header": "🔔 <b>Monitored emails ({count}/{max}):</b>\n\n",
        "mymonitors_item": (
            "• <code>{email}</code>\n"
            "  Breaches: {breaches} | Pastes: {pastes} | Last check: {last}\n\n"
        ),
        "mymonitors_hint": "Remove with <code>/unmonitor email@example.com</code>",

        # --- Cancel / Errors ---
        "cancel":         "❌ Operation cancelled.",
        "user_not_found": "❌ Error: user not found.",

        # --- Scheduler notifications ---
        "alert_header":      "🚨 <b>NEW BREACH DETECTED!</b>\n\n📧 Email: <code>{email}</code>\n\n",
        "alert_breaches":    "🔓 <b>+{count} new breach(es):</b>\n",
        "alert_breach_item": "• <b>{name}</b> ({date})\n  Affected accounts: {records}\n",
        "alert_pastes":      "📋 <b>+{count} new paste(s) detected</b>\n\n",
        "alert_actions": (
            "<b>🛡️ Recommended actions:</b>\n"
            "1️⃣ Change your password immediately\n"
            "2️⃣ Enable two-factor authentication (2FA)\n"
            "3️⃣ Monitor your account for suspicious activity\n\n"
            "Use /check to see all breaches in detail.\n\n"
            "📢 Stay updated: <a href='https://t.me/HIBP_updates'>@HIBP_updates</a>"
        ),
    },
}


def t(key: str, lang: str = "it", **kwargs: Any) -> str:
    """
    Return the translated string for `key` in `lang`.
    Falls back to Italian if the key is missing in the requested language.
    Interpolates **kwargs using str.format().
    """
    lang = lang if lang in STRINGS else "it"
    text: str = STRINGS[lang].get(key) or STRINGS["it"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
