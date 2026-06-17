"""
=============================================================
  ADMIN TRAINING ACADEMY — training.py
  Drop-in module for bot.py
  
  INTEGRATION STEPS (3 lines in bot.py):
    1. At the top, add:      from training import TrainingDB, setup_training_commands, init_training_db
    2. After init_db():      init_training_db()
    3. After bot is built:   setup_training_commands(bot, firebase_db)
=============================================================
"""

import discord
from discord import app_commands
import sqlite3
import json
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# ── shared DB path (same file as bot.py) ──────────────────────────────────────
DB_PATH = "bot_data.db"

# ── Exam cooldown (hours between retakes) ────────────────────────────────────
EXAM_COOLDOWN_HOURS = 24

# =============================================================================
# QUESTION BANK
# =============================================================================

CATEGORIES = {
    1: "Professionalism",
    2: "Rules",
    3: "How to Act",
    4: "Duties",
    5: "Final Exam",
}

# Each question:  {"q": text, "options": [A,B,C,D], "answer": 0-3, "explanation": text, "category": int}

QUESTION_BANK: List[Dict] = [

    # ── CATEGORY 1: PROFESSIONALISM ──────────────────────────────────────────

    {"q": "A member is being rude to you in a support ticket. What is the best approach?",
     "options": ["Respond with equal hostility to show authority",
                 "Remain calm, address their issue professionally and set a polite boundary",
                 "Ignore the ticket entirely",
                 "Immediately ban them for being disrespectful"],
     "answer": 1,
     "explanation": "Admins represent the staff team at all times. Staying calm de-escalates the situation and reflects well on the server.",
     "category": 1},

    {"q": "You disagree with a decision made by a senior admin in a staff channel. What should you do?",
     "options": ["Argue loudly in the public channel to get member support",
                 "Ignore it and do whatever you think is right",
                 "Raise your concern respectfully in the staff channel or DM the senior admin privately",
                 "Make passive-aggressive comments in general chat"],
     "answer": 2,
     "explanation": "Disagreements should be handled professionally in private staff spaces, not escalated publicly.",
     "category": 1},

    {"q": "Which of the following best demonstrates professional behaviour as an admin?",
     "options": ["Joking about other members behind their backs in staff chat",
                 "Treating every member with equal respect regardless of their rank or history",
                 "Only helping members you personally like",
                 "Using your admin role to gain advantages in server events"],
     "answer": 1,
     "explanation": "Fair treatment of all members — without bias — is a cornerstone of professional administration.",
     "category": 1},

    {"q": "A friend of yours who is a member breaks a rule. How should you handle it?",
     "options": ["Warn them privately and pretend it didn't happen",
                 "Give them an extra warning because they're new",
                 "Apply the same punishment you would give any other member",
                 "Ask another admin to deal with it so you don't have to"],
     "answer": 2,
     "explanation": "Consistent enforcement regardless of personal relationships is essential to fair administration. Favouritism damages trust.",
     "category": 1},

    {"q": "You are having a rough personal day and feel irritable. A member opens a ticket with a complaint. What is the most professional action?",
     "options": ["Close the ticket and return to it when you're in a better mood",
                 "Handle the ticket as professionally as you normally would, putting your personal feelings aside",
                 "Give a short, blunt response to get rid of the ticket quickly",
                 "Ask the member to come back later"],
     "answer": 1,
     "explanation": "Professionalism means separating personal mood from your duties. Members deserve consistent quality support.",
     "category": 1},

    {"q": "An admin should use their elevated permissions to:",
     "options": ["Access private member DMs to 'check for rule breaks'",
                 "Give friends early access to announcements",
                 "Moderate the server according to its rules and protect the community",
                 "Settle personal arguments by muting people who disagree with them"],
     "answer": 2,
     "explanation": "Admin permissions exist to serve the community — abusing them for personal gain or convenience is a serious breach of conduct.",
     "category": 1},

    {"q": "A member publicly criticises the staff team in general chat. What is the best response?",
     "options": ["Mute them immediately so they stop",
                 "Argue back to defend yourself",
                 "Acknowledge their concern calmly, invite them to open a ticket, and keep the public channel calm",
                 "Delete their message and warn them for disrespect"],
     "answer": 2,
     "explanation": "Engaging calmly and redirecting to proper feedback channels shows maturity and keeps public spaces civil.",
     "category": 1},

    {"q": "Maintaining a positive attitude as staff means:",
     "options": ["Pretending everything is fine even when things are genuinely wrong",
                 "Approaching situations constructively, supporting members, and contributing positively to the team",
                 "Always agreeing with senior admins even if you have concerns",
                 "Only being positive in public channels and venting in staff chat"],
     "answer": 1,
     "explanation": "A positive attitude is constructive and genuine — it means being solution-focused and supportive, not suppressing legitimate concerns.",
     "category": 1},

    # ── CATEGORY 2: RULES ────────────────────────────────────────────────────

    {"q": "A member sends a link to an unverified external Discord server. The rules say no advertising without permission. What do you do?",
     "options": ["Delete the message and ban them immediately",
                 "Warn them — it's likely their first offence and may have been accidental",
                 "Allow it since it's just a Discord link",
                 "DM them asking why they posted it before taking any action"],
     "answer": 1,
     "explanation": "A first-offence advertising rule break typically warrants a warning, with escalation only if it continues.",
     "category": 2},

    {"q": "What is the correct order of escalation for most rule violations?",
     "options": ["Ban → Mute → Warn → Kick",
                 "Warn → Mute → Kick → Ban",
                 "Kick → Ban → Warn → Mute",
                 "Mute → Warn → Kick → Ban"],
     "answer": 1,
     "explanation": "The standard escalation path is: Warn → Mute → Kick → Ban, giving members opportunities to correct their behaviour.",
     "category": 2},

    {"q": "Two members argue about whether a specific message breaks the rules. As an admin, you should:",
     "options": ["Side with whichever member has been here longer",
                 "Check the rules yourself, and if it genuinely breaks them, enforce consistently regardless of who it is",
                 "Do nothing since they're still debating it",
                 "Ask the member if they think they broke the rules"],
     "answer": 1,
     "explanation": "Rule enforcement must be consistent and objective. Admins check the rules, not opinions.",
     "category": 2},

    {"q": "Why is documenting moderation actions important?",
     "options": ["It's unnecessary — experienced admins remember everything",
                 "To share in public chat to shame rule-breakers",
                 "To maintain a consistent record so all staff can see prior actions and enforce fairly",
                 "Only bans need to be documented"],
     "answer": 2,
     "explanation": "A documented history means every admin can make informed decisions and patterns of behaviour can be identified.",
     "category": 2},

    {"q": "A member receives their third warning for the same offence. According to standard escalation, what is the appropriate next step?",
     "options": ["Issue a fourth warning", "Mute them", "Kick them", "Permanently ban them"],
     "answer": 1,
     "explanation": "After repeated warnings for the same behaviour, escalating to a mute is the standard next step.",
     "category": 2},

    {"q": "A senior admin gives a member a ban you believe was unfair. What should you do?",
     "options": ["Unban them yourself without telling anyone",
                 "Agree with the ban publicly even if you disagree",
                 "Raise your concern with the senior admin or a higher authority through proper channels",
                 "Tell the banned member they were treated unfairly"],
     "answer": 2,
     "explanation": "Staff accountability runs both ways. Concerns about unfair moderation should be raised internally through proper channels.",
     "category": 2},

    {"q": "When should a permanent ban be issued rather than a temporary one?",
     "options": ["Any time someone is rude",
                 "For severe violations such as posting illegal content, extreme harassment, or after exhausting all other escalation steps",
                 "Whenever an admin feels the member is annoying",
                 "Only when a senior admin approves it first"],
     "answer": 1,
     "explanation": "Permanent bans are reserved for the most serious violations or when all lesser punishments have failed to deter behaviour.",
     "category": 2},

    {"q": "A member claims they didn't know a rule existed. How should you respond?",
     "options": ["Reverse the punishment entirely since they didn't know",
                 "Acknowledge they may not have known, but still apply the appropriate action — ignorance of the rules is not an exemption",
                 "Give them a free pass but log the warning",
                 "Ban them for not reading the rules"],
     "answer": 1,
     "explanation": "Rules apply regardless of awareness. You may acknowledge the situation with empathy while still enforcing consistently.",
     "category": 2},

    # ── CATEGORY 3: HOW TO ACT ────────────────────────────────────────────────

    {"q": "Two members are arguing over a dispute in general chat. Before acting, an admin should:",
     "options": ["Side with whoever messaged you first",
                 "Read the full conversation, gather context, and intervene calmly",
                 "Mute both members immediately to end the argument",
                 "Ignore it and hope it resolves itself"],
     "answer": 1,
     "explanation": "Acting without context often makes situations worse. Gathering evidence first ensures fair, informed decisions.",
     "category": 3},

    {"q": "A member accuses another member of harassment, but the accused says the first member started it. You should:",
     "options": ["Believe whoever sent the report first",
                 "Review chat logs and any evidence before making a decision",
                 "Dismiss the report since both sides are blaming each other",
                 "Punish both members equally without investigation"],
     "answer": 1,
     "explanation": "Remaining neutral and evidence-based is critical. Never decide based on who reported first or personal impressions.",
     "category": 3},

    {"q": "A member is becoming increasingly aggressive in a ticket. The best de-escalation approach is:",
     "options": ["Match their energy to show you won't be pushed around",
                 "Close the ticket with no response",
                 "Stay calm, use measured language, acknowledge their frustration, and steer toward resolution",
                 "Escalate their punishment immediately"],
     "answer": 2,
     "explanation": "Calm, measured responses lower tension. Matching aggression or dismissing the person typically escalates the situation.",
     "category": 3},

    {"q": "You are personally offended by a comment a member made. How should this affect your moderation decision?",
     "options": ["It shouldn't — decisions must be based on whether rules were broken, not personal feelings",
                 "You should be stricter since they offended a staff member",
                 "You should recuse yourself from all moderation for the rest of the day",
                 "You should give them a lighter punishment to avoid appearing biased"],
     "answer": 0,
     "explanation": "Moderation must be fact-based, not emotion-based. Personal feelings should not influence enforcement decisions.",
     "category": 3},

    {"q": "When handling a dispute between two members, neutrality means:",
     "options": ["Always splitting punishments 50/50 between both parties",
                 "Never punishing anyone to avoid appearing biased",
                 "Evaluating the evidence objectively without favouring either party",
                 "Asking other staff members to vote on who is right"],
     "answer": 2,
     "explanation": "Neutrality is about objective evaluation of evidence, not avoiding all action or splitting blame arbitrarily.",
     "category": 3},

    {"q": "A member is trying to argue with you about a moderation decision in public chat. You should:",
     "options": ["Debate with them publicly to prove your point",
                 "Ignore them completely",
                 "Redirect them politely to a ticket or DM for private discussion, and avoid a public argument",
                 "Mute them for questioning staff decisions"],
     "answer": 2,
     "explanation": "Public arguments with members are unprofessional and can inflame situations. Private channels allow proper resolution.",
     "category": 3},

    {"q": "You receive a report about a message but it has since been deleted. What is the best course of action?",
     "options": ["Ignore the report since there's no evidence",
                 "Punish the accused member based on the report alone",
                 "Check audit logs, ask if the reporter has screenshots, and explain you'll monitor the situation",
                 "Close the ticket and warn the reporter for wasting your time"],
     "answer": 2,
     "explanation": "Evidence-based decisions are essential. Exhaust all investigative options before deciding, and be transparent about limitations.",
     "category": 3},

    {"q": "Making decisions based on facts rather than emotions means:",
     "options": ["Never showing empathy to members",
                 "Basing your judgement on observable evidence and server rules, not assumptions or gut feelings",
                 "Only acting when you are 100% certain of every detail",
                 "Letting senior admins make all decisions so you don't have to feel responsible"],
     "answer": 1,
     "explanation": "Fact-based decisions are fair and defensible. Empathy is still appropriate — it just shouldn't replace evidence-based reasoning.",
     "category": 3},

    # ── CATEGORY 4: DUTIES ────────────────────────────────────────────────────

    {"q": "A support ticket has been open for 18 hours with no staff response. What should happen?",
     "options": ["Close the ticket to reduce the queue",
                 "Any available admin should pick it up and respond as soon as possible",
                 "Wait for the original admin who created the ticket to return",
                 "Ask the member to reopen a new ticket"],
     "answer": 1,
     "explanation": "Leaving members without support damages community trust. Tickets should be picked up in a timely manner by any available admin.",
     "category": 4},

    {"q": "While monitoring general chat, you notice a rising argument that hasn't broken any rules yet. You should:",
     "options": ["Wait until a rule is broken before intervening",
                 "Send a warning message to both parties immediately",
                 "Monitor closely and consider a calm, early intervention to prevent escalation",
                 "Mute the channel until they calm down"],
     "answer": 2,
     "explanation": "Proactive monitoring means catching problems early. A calm, early intervention can prevent full rule breaks.",
     "category": 4},

    {"q": "When should a moderation action be recorded?",
     "options": ["Only for bans and kicks",
                 "Only when a senior admin asks for records",
                 "After every moderation action, including warnings and mutes",
                 "Recording is optional and left to admin preference"],
     "answer": 2,
     "explanation": "All moderation actions should be logged so that the full history of a member's behaviour is visible to all staff.",
     "category": 4},

    {"q": "A member asks you a question outside your area of expertise. The best response is to:",
     "options": ["Give your best guess without flagging uncertainty",
                 "Ignore the question",
                 "Tell them you're not sure and direct them to the right resource or staff member",
                 "Close their ticket and mark it resolved"],
     "answer": 2,
     "explanation": "Honesty and redirection serve members better than guessing. Knowing when to escalate is part of effective admin work.",
     "category": 4},

    {"q": "Which of the following best describes the duty to 'work with other staff'?",
     "options": ["Doing all moderation yourself to avoid burdening colleagues",
                 "Communicating decisions, sharing information, and supporting each other to provide consistent moderation",
                 "Checking with every admin before taking any action",
                 "Agreeing with all staff decisions even if you have concerns"],
     "answer": 1,
     "explanation": "Effective teams communicate and share context. Consistency across the team requires regular coordination.",
     "category": 4},

    {"q": "You notice a member has received 3 warnings in the past week from different admins for similar behaviour. You should:",
     "options": ["Ignore it since each admin handled their own incident",
                 "Warn them a 4th time yourself to continue the pattern",
                 "Flag the pattern to the team and consider whether escalation is appropriate",
                 "Ban them immediately since it keeps happening"],
     "answer": 2,
     "explanation": "Identifying patterns across incidents is key to proactive moderation. Team coordination prevents inconsistent enforcement.",
     "category": 4},

    {"q": "A member submits a report accusing another member of behaviour that happened outside the server. What is the appropriate response?",
     "options": ["Take immediate action since the member reported it",
                 "Explain your jurisdiction is limited to in-server behaviour, but take note if the accused also causes issues in the server",
                 "Dismiss the report entirely without explanation",
                 "Ban the accused to be safe"],
     "answer": 1,
     "explanation": "Admin authority typically extends only to in-server conduct. Being transparent about this is respectful and informative.",
     "category": 4},

    {"q": "Handling tickets effectively means:",
     "options": ["Resolving tickets as fast as possible, even if the solution is incomplete",
                 "Only handling tickets related to your personal area of expertise",
                 "Responding promptly, gathering all necessary information, and following up until resolution",
                 "Closing tickets after one response regardless of outcome"],
     "answer": 2,
     "explanation": "Quality ticket handling means thorough, followed-through support — speed matters but not at the cost of resolution quality.",
     "category": 4},
]

# A shorter "lesson" per category (shown before questions begin)
LESSONS: Dict[int, Dict] = {
    1: {
        "title": "📘 Category 1: Professionalism",
        "colour": 0x5865F2,
        "sections": [
            ("Respectful Communication", "Always address members with respect, regardless of how they speak to you. Your tone sets the standard."),
            ("Remaining Calm During Conflicts", "Take a breath before responding to difficult situations. Calm admins de-escalate; reactive admins escalate."),
            ("Avoiding Abuse of Power", "Permissions exist to protect the community, not to serve personal agendas. Never use your role to gain advantages."),
            ("Fair Treatment", "Every member receives the same standard of service. No favourites — not even friends."),
            ("Representing the Staff Team", "Everything you say publicly reflects on the entire team. Behave as if your DMs are visible to the server owner."),
            ("Positive Attitude", "Approach problems constructively. A good attitude is contagious — and so is a bad one."),
            ("Public vs Private Channels", "Maintain the same standard in both. Staff channels are not a place to vent unprofessionally about members."),
        ]
    },
    2: {
        "title": "📗 Category 2: Rules",
        "colour": 0x57F287,
        "sections": [
            ("Understanding the Rules", "Know every server rule thoroughly. You cannot enforce what you don't understand."),
            ("Consistent Enforcement", "The same action must receive the same consequence, regardless of who committed it."),
            ("Escalation: Warn → Mute → Kick → Ban", "Follow the escalation ladder. Jumping straight to a ban for minor offences is disproportionate."),
            ("Documentation", "Log every action. Future staff will need this history to make informed decisions."),
            ("When to Escalate to Senior Staff", "Situations involving ban appeals, ban evasion, or staff misconduct should go to a senior admin."),
            ("Staff Accountability", "Admins can make mistakes. When that happens, own it and correct it through proper channels."),
        ]
    },
    3: {
        "title": "📙 Category 3: How to Act",
        "colour": 0xFEE75C,
        "sections": [
            ("Listen Before Acting", "Read the full context before intervening. Jumping in early with incomplete information causes more harm."),
            ("Remaining Neutral", "You are not a participant in disputes — you are a mediator. Remove personal bias from your decisions."),
            ("Gathering Evidence", "Screenshots, audit logs, and message history are your tools. Always investigate before punishing."),
            ("Handling Disputes Fairly", "Apply the same criteria to both parties. Consistency is fairness."),
            ("Avoiding Arguments with Members", "You do not need to win arguments. Redirect disputes to tickets and maintain composure."),
            ("De-escalation", "Use calm, measured language. Acknowledge frustration without endorsing rule-breaking."),
            ("Facts Over Feelings", "Base decisions on observable evidence. Personal feelings are not a moderation tool."),
        ]
    },
    4: {
        "title": "📕 Category 4: Duties",
        "colour": 0xED4245,
        "sections": [
            ("Handling Tickets", "Respond promptly, gather context, follow up, and close only when fully resolved."),
            ("Responding to Reports", "Every report deserves acknowledgment. Even if no action is taken, communicate your decision."),
            ("Monitoring Chats", "Active presence prevents issues. Catch problems early before they escalate."),
            ("Assisting Members", "Helping members is the core of your role. Be approachable and informative."),
            ("Working with Other Staff", "Share decisions and context with your team. Consistent moderation requires coordination."),
            ("Recording Actions", "Log every moderation action in the appropriate channel or system."),
            ("Proactive Problem Identification", "Notice patterns before they become incidents. Preventive moderation is the best moderation."),
        ]
    },
}


# =============================================================================
# DATABASE
# =============================================================================

def init_training_db():
    """Add training tables to the existing bot database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            user_id     INTEGER NOT NULL,
            guild_id    INTEGER NOT NULL,
            current_category    INTEGER DEFAULT 1,
            completed_categories TEXT DEFAULT '[]',
            category_scores     TEXT DEFAULT '{}',
            paused              INTEGER DEFAULT 0,
            paused_step         TEXT DEFAULT NULL,
            started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exam_status         TEXT DEFAULT 'not_started',
            exam_score          INTEGER DEFAULT 0,
            exam_attempts       INTEGER DEFAULT 0,
            exam_last_attempt   TIMESTAMP DEFAULT NULL,
            certified           INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    """)

    # Per-question answer log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_answers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            guild_id    INTEGER NOT NULL,
            category    INTEGER NOT NULL,
            question_idx INTEGER NOT NULL,
            correct     INTEGER NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[TRAINING] ✅ Training tables ready")


class TrainingDB:
    """All database operations for the training system."""

    @staticmethod
    def get_progress(user_id: int, guild_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM training_progress WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "user_id": row[0],
            "guild_id": row[1],
            "current_category": row[2],
            "completed_categories": json.loads(row[3]),
            "category_scores": json.loads(row[4]),
            "paused": bool(row[5]),
            "paused_step": json.loads(row[6]) if row[6] else None,
            "started_at": row[7],
            "last_active": row[8],
            "exam_status": row[9],
            "exam_score": row[10],
            "exam_attempts": row[11],
            "exam_last_attempt": row[12],
            "certified": bool(row[13]),
        }

    @staticmethod
    def create_progress(user_id: int, guild_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_progress (user_id, guild_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, guild_id) DO NOTHING
        """, (user_id, guild_id))
        conn.commit()
        conn.close()

    @staticmethod
    def update_progress(user_id: int, guild_id: int, **kwargs):
        if not kwargs:
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        set_clauses = []
        values = []
        for key, val in kwargs.items():
            if isinstance(val, (dict, list)):
                val = json.dumps(val)
            set_clauses.append(f"{key}=?")
            values.append(val)
        set_clauses.append("last_active=CURRENT_TIMESTAMP")
        sql = f"UPDATE training_progress SET {', '.join(set_clauses)} WHERE user_id=? AND guild_id=?"
        values += [user_id, guild_id]
        cursor.execute(sql, values)
        conn.commit()
        conn.close()

    @staticmethod
    def reset_progress(user_id: int, guild_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM training_progress WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
        cursor.execute(
            "DELETE FROM training_answers WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def log_answer(user_id: int, guild_id: int, category: int, question_idx: int, correct: bool):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_answers (user_id, guild_id, category, question_idx, correct)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, category, question_idx, int(correct)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_answer_stats(user_id: int, guild_id: int) -> Dict:
        """Returns per-category correct/incorrect counts."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, correct, COUNT(*) FROM training_answers
            WHERE user_id=? AND guild_id=?
            GROUP BY category, correct
        """, (user_id, guild_id))
        rows = cursor.fetchall()
        conn.close()
        stats = {}
        for cat, correct, count in rows:
            if cat not in stats:
                stats[cat] = {"correct": 0, "incorrect": 0}
            key = "correct" if correct else "incorrect"
            stats[cat][key] = count
        return stats

    @staticmethod
    def get_all_trainees(guild_id: int) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM training_progress WHERE guild_id=? ORDER BY certified DESC, exam_score DESC",
            (guild_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "user_id": row[0],
                "guild_id": row[1],
                "current_category": row[2],
                "completed_categories": json.loads(row[3]),
                "category_scores": json.loads(row[4]),
                "paused": bool(row[5]),
                "started_at": row[7],
                "last_active": row[8],
                "exam_status": row[9],
                "exam_score": row[10],
                "exam_attempts": row[11],
                "exam_last_attempt": row[12],
                "certified": bool(row[13]),
            })
        return result


# =============================================================================
# HELPERS
# =============================================================================

def progress_bar(filled: int, total: int, length: int = 10) -> str:
    """Unicode progress bar."""
    filled_count = round(length * filled / max(total, 1))
    return "█" * filled_count + "░" * (length - filled_count)


def get_completion_pct(progress: Dict) -> int:
    completed = len(progress["completed_categories"])
    # 4 categories + exam = 5 stages
    exam_bonus = 1 if progress["exam_status"] == "passed" else 0
    return min(100, round((completed + exam_bonus) / 5 * 100))


def get_category_questions(category: int) -> List[Dict]:
    """Return all questions for a given category (1-4)."""
    return [q for q in QUESTION_BANK if q["category"] == category]


def build_exam_questions(count: int = 25) -> List[Dict]:
    """Randomly select questions across all 4 lesson categories."""
    pool = [q for q in QUESTION_BANK if q["category"] in (1, 2, 3, 4)]
    return random.sample(pool, min(count, len(pool)))


def can_retake_exam(progress: Dict) -> (bool, Optional[str]):
    """Returns (can_retake, reason_if_not)."""
    if not progress["exam_last_attempt"]:
        return True, None
    last = datetime.fromisoformat(progress["exam_last_attempt"])
    eligible_at = last + timedelta(hours=EXAM_COOLDOWN_HOURS)
    if datetime.utcnow() >= eligible_at:
        return True, None
    remaining = eligible_at - datetime.utcnow()
    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes = remainder // 60
    return False, f"{hours}h {minutes}m"


# =============================================================================
# UI COMPONENTS
# =============================================================================

class LessonView(discord.ui.View):
    """Displays a lesson with a 'Begin Quiz' button."""

    def __init__(self, user_id: int, guild_id: int, category: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category = category

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This training session belongs to someone else.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Begin Quiz ▶", style=discord.ButtonStyle.primary, emoji="📝")
    async def begin_quiz(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        questions = get_category_questions(self.category)
        # Save paused_step so /training continue works
        TrainingDB.update_progress(
            self.user_id, self.guild_id,
            paused_step={"stage": "quiz", "category": self.category, "q_index": 0,
                         "score": 0, "questions": [QUESTION_BANK.index(q) for q in questions]}
        )
        await interaction.response.edit_message(
            embed=build_question_embed(questions[0], self.category, 1, len(questions)),
            view=QuizView(self.user_id, self.guild_id, self.category, questions, 0, 0)
        )


class QuizView(discord.ui.View):
    """A/B/C/D answer buttons for quiz questions."""

    LABELS = ["A", "B", "C", "D"]
    STYLES = [discord.ButtonStyle.secondary] * 4

    def __init__(self, user_id: int, guild_id: int, category: int,
                 questions: List[Dict], q_index: int, score: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category = category
        self.questions = questions
        self.q_index = q_index
        self.score = score
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        q = self.questions[self.q_index]
        for i, opt in enumerate(q["options"]):
            btn = discord.ui.Button(
                label=f"{self.LABELS[i]}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"ans_{i}",
                row=0
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This isn't your training session.", ephemeral=True)
                return

            # Defer immediately to avoid the 3-second Discord timeout
            await interaction.response.defer()

            q = self.questions[self.q_index]
            correct = (choice == q["answer"])
            new_score = self.score + (1 if correct else 0)

            # Log answer
            TrainingDB.log_answer(
                self.user_id, self.guild_id,
                self.category, self.q_index, correct
            )

            # Build feedback embed
            embed = discord.Embed(
                title="✅ Correct!" if correct else "❌ Incorrect",
                colour=discord.Colour.green() if correct else discord.Colour.red()
            )
            selected_label = self.LABELS[choice]
            correct_label = self.LABELS[q["answer"]]
            embed.add_field(name="Your answer", value=f"**{selected_label}** — {q['options'][choice]}", inline=False)
            if not correct:
                embed.add_field(name="Correct answer", value=f"**{correct_label}** — {q['options'][q['answer']]}", inline=False)
            embed.add_field(name="💡 Explanation", value=q["explanation"], inline=False)
            embed.set_footer(text=f"Question {self.q_index + 1}/{len(self.questions)} | Score so far: {new_score}/{self.q_index + 1}")

            next_index = self.q_index + 1
            if next_index >= len(self.questions):
                # Category complete
                await interaction.edit_original_response(embed=embed, view=CategoryCompleteView(
                    self.user_id, self.guild_id, self.category, new_score, len(self.questions)
                ))
            else:
                # Next question
                TrainingDB.update_progress(
                    self.user_id, self.guild_id,
                    paused_step={"stage": "quiz", "category": self.category, "q_index": next_index,
                                 "score": new_score, "questions": [QUESTION_BANK.index(q2) for q2 in self.questions]}
                )
                await interaction.edit_original_response(
                    embed=embed,
                    view=NextQuestionView(self.user_id, self.guild_id, self.category,
                                         self.questions, next_index, new_score)
                )
        return callback


class NextQuestionView(discord.ui.View):
    """Shown after feedback — single 'Next Question' button."""

    def __init__(self, user_id, guild_id, category, questions, next_index, score):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category = category
        self.questions = questions
        self.next_index = next_index
        self.score = score

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Next Question ▶", style=discord.ButtonStyle.primary)
    async def next_q(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        q = self.questions[self.next_index]
        await interaction.response.edit_message(
            embed=build_question_embed(q, self.category, self.next_index + 1, len(self.questions)),
            view=QuizView(self.user_id, self.guild_id, self.category,
                          self.questions, self.next_index, self.score)
        )


class CategoryCompleteView(discord.ui.View):
    """Shown when a category quiz finishes. Saves score and unlocks next."""

    def __init__(self, user_id, guild_id, category, score, total):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category = category
        self.score = score
        self.total = total
        self._save()

    def _save(self):
        progress = TrainingDB.get_progress(self.user_id, self.guild_id)
        if not progress:
            return
        completed = progress["completed_categories"]
        if self.category not in completed:
            completed.append(self.category)
        scores = progress["category_scores"]
        scores[str(self.category)] = {"score": self.score, "total": self.total}
        next_cat = self.category + 1 if self.category < 5 else self.category
        TrainingDB.update_progress(
            self.user_id, self.guild_id,
            completed_categories=completed,
            category_scores=scores,
            current_category=next_cat,
            paused_step=None,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Continue Training ▶", style=discord.ButtonStyle.success, emoji="🎓")
    async def continue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        progress = TrainingDB.get_progress(self.user_id, self.guild_id)
        next_cat = self.category + 1

        if next_cat == 5:
            # Move to final exam
            can, cooldown_msg = can_retake_exam(progress)
            if not can:
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        title="⏳ Exam Cooldown",
                        description=f"You can retake the Final Exam in **{cooldown_msg}**.",
                        colour=discord.Colour.orange()
                    ),
                    view=None
                )
                return
            await start_exam(interaction, self.user_id, self.guild_id, edit=True)
        elif next_cat <= 4:
            await show_lesson(interaction, self.user_id, self.guild_id, next_cat, edit=True)
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(title="🎉 Training Complete!", description="All categories done. Use `/training certificate` to view your result.", colour=discord.Colour.gold()),
                view=None
            )


class ExamAnswerView(discord.ui.View):
    """Answer buttons for the final exam."""

    LABELS = ["A", "B", "C", "D"]

    def __init__(self, user_id, guild_id, questions, q_index, score, wrong_answers):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.guild_id = guild_id
        self.questions = questions
        self.q_index = q_index
        self.score = score
        self.wrong_answers = wrong_answers  # list of dicts for review
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for i in range(len(self.questions[self.q_index]["options"])):
            btn = discord.ui.Button(label=self.LABELS[i], style=discord.ButtonStyle.secondary, custom_id=f"exam_{i}", row=0)
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This isn't your exam.", ephemeral=True)
                return

            # Defer immediately to avoid the 3-second Discord timeout
            await interaction.response.defer()

            q = self.questions[self.q_index]
            correct = (choice == q["answer"])
            new_score = self.score + (1 if correct else 0)
            new_wrong = list(self.wrong_answers)
            if not correct:
                new_wrong.append({"q": q["q"], "your": q["options"][choice],
                                  "correct": q["options"][q["answer"]], "explanation": q["explanation"]})

            feedback = discord.Embed(
                title="✅ Correct!" if correct else "❌ Incorrect",
                colour=discord.Colour.green() if correct else discord.Colour.red()
            )
            feedback.add_field(name="Your answer", value=f"**{self.LABELS[choice]}** — {q['options'][choice]}", inline=False)
            if not correct:
                feedback.add_field(name="Correct answer", value=f"**{self.LABELS[q['answer']]}** — {q['options'][q['answer']]}", inline=False)
            feedback.add_field(name="💡", value=q["explanation"], inline=False)
            feedback.set_footer(text=f"Exam Q{self.q_index + 1}/{len(self.questions)} | Running score: {new_score}")

            next_index = self.q_index + 1
            if next_index >= len(self.questions):
                # Exam done
                await finish_exam(interaction, self.user_id, self.guild_id, new_score, len(self.questions), new_wrong, feedback)
            else:
                await interaction.edit_original_response(
                    embed=feedback,
                    view=ExamNextView(self.user_id, self.guild_id, self.questions, next_index, new_score, new_wrong)
                )
        return callback


class ExamNextView(discord.ui.View):
    """'Next Question' button during exam."""

    def __init__(self, user_id, guild_id, questions, next_index, score, wrong_answers):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.guild_id = guild_id
        self.questions = questions
        self.next_index = next_index
        self.score = score
        self.wrong_answers = wrong_answers

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Next Question ▶", style=discord.ButtonStyle.primary)
    async def next_q(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        q = self.questions[self.next_index]
        embed = build_question_embed(q, 5, self.next_index + 1, len(self.questions), exam=True)
        await interaction.response.edit_message(
            embed=embed,
            view=ExamAnswerView(self.user_id, self.guild_id, self.questions,
                                self.next_index, self.score, self.wrong_answers)
        )


class ProgressView(discord.ui.View):
    """Paginated progress board."""

    def __init__(self, pages: List[discord.Embed]):
        super().__init__(timeout=120)
        self.pages = pages
        self.current = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.current == 0
        self.next_btn.disabled = self.current >= len(self.pages) - 1

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)


# =============================================================================
# EMBED BUILDERS
# =============================================================================

def build_lesson_embed(category: int) -> discord.Embed:
    lesson = LESSONS[category]
    embed = discord.Embed(
        title=lesson["title"],
        colour=lesson["colour"],
        description="Read through this lesson carefully before proceeding to the quiz."
    )
    for name, value in lesson["sections"]:
        embed.add_field(name=f"▸ {name}", value=value, inline=False)
    embed.set_footer(text=f"Category {category} of 4 | Press 'Begin Quiz' when ready")
    return embed


def build_question_embed(q: Dict, category: int, q_num: int, total: int, exam: bool = False) -> discord.Embed:
    label = "🎓 Final Exam" if exam else f"📝 {CATEGORIES[category]} Quiz"
    embed = discord.Embed(
        title=f"{label} — Question {q_num}/{total}",
        description=f"**{q['q']}**",
        colour=discord.Colour.blurple() if exam else discord.Colour.blue()
    )
    for i, opt in enumerate(q["options"]):
        embed.add_field(name=f"{['A','B','C','D'][i]}.", value=opt, inline=False)
    embed.set_footer(text="Select your answer below")
    return embed


async def show_lesson(interaction: discord.Interaction, user_id: int, guild_id: int, category: int, edit: bool = False):
    embed = build_lesson_embed(category)
    view = LessonView(user_id, guild_id, category)
    TrainingDB.update_progress(user_id, guild_id, current_category=category,
                               paused_step={"stage": "lesson", "category": category})
    if edit:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def start_exam(interaction: discord.Interaction, user_id: int, guild_id: int, edit: bool = False):
    questions = build_exam_questions(25)
    q = questions[0]
    embed = build_question_embed(q, 5, 1, len(questions), exam=True)
    view = ExamAnswerView(user_id, guild_id, questions, 0, 0, [])

    # Mark exam started
    TrainingDB.update_progress(
        user_id, guild_id,
        exam_status="in_progress",
        exam_last_attempt=datetime.utcnow().isoformat(),
        paused_step=None
    )
    if edit:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def finish_exam(interaction: discord.Interaction, user_id: int, guild_id: int,
                      score: int, total: int, wrong_answers: List[Dict], final_feedback: discord.Embed):
    pct = round(score / total * 100)
    passed = pct >= 80
    status = "passed" if passed else "failed"

    # Update DB
    progress = TrainingDB.get_progress(user_id, guild_id)
    attempts = (progress["exam_attempts"] or 0) + 1
    TrainingDB.update_progress(
        user_id, guild_id,
        exam_status=status,
        exam_score=pct,
        exam_attempts=attempts,
        exam_last_attempt=datetime.utcnow().isoformat(),
        certified=int(passed),
        paused_step=None
    )

    # Show feedback then result
    result_embed = discord.Embed(
        title="🎉 PASSED — Certified!" if passed else "❌ Failed — Please Retake",
        colour=discord.Colour.gold() if passed else discord.Colour.red(),
        description=(
            f"**Score: {score}/{total} ({pct}%)**\n\n"
            + ("✅ Congratulations! You have passed the Final Exam and earned your certification." if passed
               else f"You need **80%** to pass. You can retake after **{EXAM_COOLDOWN_HOURS} hours**.")
        )
    )
    bar = progress_bar(pct, 100, 15)
    result_embed.add_field(name="Progress", value=f"`{bar}` {pct}%", inline=False)

    if wrong_answers:
        # Show up to 5 wrong answers in embed
        review_text = ""
        for i, wa in enumerate(wrong_answers[:5]):
            review_text += f"**Q: {wa['q'][:80]}...**\n✗ You: {wa['your']}\n✓ Correct: {wa['correct']}\n💡 {wa['explanation']}\n\n"
        if len(wrong_answers) > 5:
            review_text += f"*...and {len(wrong_answers) - 5} more. Use `/training progress` to review.*"
        result_embed.add_field(name=f"❌ Incorrect Answers ({len(wrong_answers)})", value=review_text, inline=False)

    await interaction.edit_original_response(embed=result_embed, view=None)


# =============================================================================
# SLASH COMMANDS
# =============================================================================

def setup_training_commands(bot, firebase_db_ref=None):
    """
    Register all /training and /progress slash commands with the bot.
    Call this ONCE after your bot object is created, e.g.:
        setup_training_commands(bot, firebase_db)
    """

    training_group = app_commands.Group(name="training", description="Admin Training Academy")

    # ── /training start ──────────────────────────────────────────────────────
    @training_group.command(name="start", description="Begin your admin training")
    async def training_start(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        progress = TrainingDB.get_progress(user_id, guild_id)

        if progress and len(progress["completed_categories"]) > 0:
            embed = discord.Embed(
                title="⚠️ Training Already In Progress",
                description="You already have active training. Use `/training continue` to pick up where you left off, or `/training reset` to start over (admin only).",
                colour=discord.Colour.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        TrainingDB.create_progress(user_id, guild_id)

        welcome = discord.Embed(
            title="🎓 Welcome to the Admin Training Academy",
            colour=discord.Colour.blurple(),
            description=(
                "This training programme will prepare you for your role as a server administrator.\n\n"
                "**Training Structure:**\n"
                "📘 Category 1: Professionalism\n"
                "📗 Category 2: Rules\n"
                "📙 Category 3: How to Act\n"
                "📕 Category 4: Duties\n"
                "🎓 Final Exam (80% pass mark required)\n\n"
                "Each category includes a lesson and a quiz. You must pass each category to unlock the next.\n\n"
                "*Your progress is saved automatically after every answer.*"
            )
        )
        welcome.set_footer(text="Press 'Begin Lesson' to start Category 1")

        class StartView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            @discord.ui.button(label="Begin Lesson 1 ▶", style=discord.ButtonStyle.success, emoji="📘")
            async def begin(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != user_id:
                    await btn_interaction.response.send_message("This isn't your session.", ephemeral=True)
                    return
                self.stop()
                await show_lesson(btn_interaction, user_id, guild_id, 1, edit=True)

        await interaction.response.send_message(embed=welcome, view=StartView(), ephemeral=True)

    # ── /training continue ────────────────────────────────────────────────────
    @training_group.command(name="continue", description="Continue your training from where you left off")
    async def training_continue(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        progress = TrainingDB.get_progress(user_id, guild_id)

        if not progress:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ No Training Found", description="Use `/training start` to begin.", colour=discord.Colour.red()),
                ephemeral=True
            )
            return

        step = progress.get("paused_step")

        # Determine where to resume
        if progress["exam_status"] in ("not_started", "in_progress") and len(progress["completed_categories"]) >= 4:
            # Resume exam
            can, cooldown_msg = can_retake_exam(progress)
            if not can:
                await interaction.response.send_message(
                    embed=discord.Embed(title="⏳ Exam Cooldown", description=f"Retake available in **{cooldown_msg}**.", colour=discord.Colour.orange()),
                    ephemeral=True
                )
                return
            await start_exam(interaction, user_id, guild_id)
        elif step and step.get("stage") == "quiz":
            # Resume mid-quiz
            cat = step["category"]
            q_index = step["q_index"]
            score = step["score"]
            questions = [QUESTION_BANK[i] for i in step["questions"]]
            q = questions[q_index]
            await interaction.response.send_message(
                embed=build_question_embed(q, cat, q_index + 1, len(questions)),
                view=QuizView(user_id, guild_id, cat, questions, q_index, score),
                ephemeral=True
            )
        else:
            # Resume lesson
            cat = progress["current_category"]
            if cat > 4:
                if progress["exam_status"] == "passed":
                    await interaction.response.send_message(
                        embed=discord.Embed(title="🏆 Training Complete", description="You are certified! Use `/training certificate` to view your certificate.", colour=discord.Colour.gold()),
                        ephemeral=True
                    )
                else:
                    await start_exam(interaction, user_id, guild_id)
            else:
                await show_lesson(interaction, user_id, guild_id, cat)

    # ── /training pause ───────────────────────────────────────────────────────
    @training_group.command(name="pause", description="Pause your training session")
    async def training_pause(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        progress = TrainingDB.get_progress(user_id, guild_id)

        if not progress:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ No Active Training", description="Use `/training start` to begin.", colour=discord.Colour.red()),
                ephemeral=True
            )
            return

        TrainingDB.update_progress(user_id, guild_id, paused=1)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏸ Training Paused",
                description="Your progress has been saved. Use `/training continue` to resume at any time.",
                colour=discord.Colour.orange()
            ),
            ephemeral=True
        )

    # ── /training progress ────────────────────────────────────────────────────
    @training_group.command(name="progress", description="View your training progress")
    async def training_progress_cmd(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        progress = TrainingDB.get_progress(user_id, guild_id)

        if not progress:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ No Training Found", description="Use `/training start` to begin.", colour=discord.Colour.red()),
                ephemeral=True
            )
            return

        stats = TrainingDB.get_answer_stats(user_id, guild_id)
        pct = get_completion_pct(progress)
        bar = progress_bar(pct, 100, 15)

        embed = discord.Embed(
            title=f"📊 Training Progress — {interaction.user.display_name}",
            colour=discord.Colour.blurple()
        )
        embed.add_field(name="Overall Completion", value=f"`{bar}` {pct}%", inline=False)

        for cat_id, cat_name in CATEGORIES.items():
            if cat_id == 5:
                continue
            done = cat_id in progress["completed_categories"]
            score_info = progress["category_scores"].get(str(cat_id))
            if done and score_info:
                val = f"✅ Complete — {score_info['score']}/{score_info['total']} ({round(score_info['score']/score_info['total']*100)}%)"
            elif cat_id == progress["current_category"] and not done:
                val = "🔄 In Progress"
            elif cat_id < progress["current_category"]:
                val = "✅ Complete"
            else:
                val = "🔒 Locked"
            embed.add_field(name=f"{'📘📗📙📕'.split()[cat_id-1] if cat_id <= 4 else ''} {cat_name}", value=val, inline=True)

        # Exam status
        exam_map = {"not_started": "⬜ Not Started", "in_progress": "🔄 In Progress", "passed": "✅ Passed", "failed": "❌ Failed"}
        embed.add_field(
            name="🎓 Final Exam",
            value=f"{exam_map.get(progress['exam_status'], '⬜ Not Started')} — Score: {progress['exam_score']}%",
            inline=False
        )
        cert = "🏆 **CERTIFIED**" if progress["certified"] else "❌ Not Certified"
        embed.add_field(name="Certification", value=cert, inline=True)
        embed.add_field(name="Attempts", value=str(progress["exam_attempts"]), inline=True)
        embed.set_footer(text=f"Training started: {progress['started_at'][:10]} | Last active: {progress['last_active'][:10]}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /training reset ───────────────────────────────────────────────────────
    @training_group.command(name="reset", description="[Admin only] Reset a user's training progress")
    @app_commands.describe(user="The user whose training you want to reset")
    async def training_reset(interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ Permission Denied", description="Only administrators can reset training.", colour=discord.Colour.red()),
                ephemeral=True
            )
            return

        TrainingDB.reset_progress(user.id, interaction.guild.id)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔄 Training Reset",
                description=f"Training progress for **{user.display_name}** has been fully reset.",
                colour=discord.Colour.green()
            ),
            ephemeral=True
        )

    # ── /training certificate ─────────────────────────────────────────────────
    @training_group.command(name="certificate", description="View your training certificate status")
    async def training_certificate(interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        progress = TrainingDB.get_progress(user_id, guild_id)

        if not progress or not progress["certified"]:
            embed = discord.Embed(
                title="❌ Not Yet Certified",
                description=(
                    "You haven't earned your admin training certificate yet.\n\n"
                    "Complete all 4 training categories and pass the Final Exam with 80% or higher."
                ),
                colour=discord.Colour.red()
            )
            if progress:
                pct = get_completion_pct(progress)
                embed.add_field(name="Your Progress", value=f"`{progress_bar(pct, 100)}` {pct}%", inline=False)
        else:
            embed = discord.Embed(
                title="🏆 Admin Training Certificate",
                colour=discord.Colour.gold(),
                description=(
                    f"**{interaction.user.display_name}** has successfully completed the Admin Training Academy.\n\n"
                    f"✅ All categories completed\n"
                    f"🎓 Final Exam: **{progress['exam_score']}%**\n"
                    f"📅 Certified on: {progress['last_active'][:10]}"
                )
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🏆")
            embed.set_footer(text="Admin Training Academy | Official Certification")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /progress (server-wide leaderboard) ───────────────────────────────────
    @bot.tree.command(name="progress", description="[Admin only] View all trainee progress")
    @app_commands.describe(user="Optional: view detailed progress for a specific user")
    async def progress_board(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ Admin Only", description="This command is restricted to administrators.", colour=discord.Colour.red()),
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        # Single user view
        if user:
            progress = TrainingDB.get_progress(user.id, guild_id)
            if not progress:
                await interaction.response.send_message(
                    embed=discord.Embed(title="❌ No Data", description=f"{user.display_name} has not started training.", colour=discord.Colour.red()),
                    ephemeral=True
                )
                return

            stats = TrainingDB.get_answer_stats(user.id, guild_id)
            pct = get_completion_pct(progress)
            embed = discord.Embed(
                title=f"👤 Training Report — {user.display_name}",
                colour=discord.Colour.blurple()
            )
            embed.add_field(name="Completion", value=f"`{progress_bar(pct, 100)}` {pct}%", inline=False)
            for cat_id in range(1, 5):
                cat_stats = stats.get(cat_id, {"correct": 0, "incorrect": 0})
                score_info = progress["category_scores"].get(str(cat_id), {})
                done = cat_id in progress["completed_categories"]
                val = (f"✅ Score: {score_info.get('score', 0)}/{score_info.get('total', '?')}\n"
                       f"✓ {cat_stats['correct']} correct, ✗ {cat_stats['incorrect']} incorrect")
                embed.add_field(name=f"{CATEGORIES[cat_id]}", value=val if done else "🔒 Not reached", inline=True)
            embed.add_field(name="Final Exam", value=f"{progress['exam_status'].title()} — {progress['exam_score']}% ({progress['exam_attempts']} attempt(s))", inline=False)
            embed.add_field(name="Certified", value="✅ Yes" if progress["certified"] else "❌ No", inline=True)
            embed.add_field(name="Started", value=progress["started_at"][:10], inline=True)
            embed.add_field(name="Last Active", value=progress["last_active"][:10], inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Server-wide board
        trainees = TrainingDB.get_all_trainees(guild_id)
        if not trainees:
            await interaction.response.send_message(
                embed=discord.Embed(title="📊 No Trainees Yet", description="Nobody has started training yet.", colour=discord.Colour.greyple()),
                ephemeral=True
            )
            return

        # Sort by completion pct desc
        trainees.sort(key=lambda t: get_completion_pct(t), reverse=True)

        # Stats header
        total = len(trainees)
        certified = sum(1 for t in trainees if t["certified"])
        passed = sum(1 for t in trainees if t["exam_status"] == "passed")
        failed = sum(1 for t in trainees if t["exam_status"] == "failed")

        # Paginate — 10 per page
        page_size = 10
        pages = []
        for page_start in range(0, total, page_size):
            page_trainees = trainees[page_start:page_start + page_size]
            page_num = page_start // page_size + 1
            total_pages = math.ceil(total / page_size)

            embed = discord.Embed(
                title="📊 Admin Training Progress Board",
                colour=discord.Colour.blurple()
            )
            embed.add_field(
                name="Server Statistics",
                value=f"👥 Trainees: **{total}** | 🏆 Certified: **{certified}** | ✅ Exam Passed: **{passed}** | ❌ Failed: **{failed}**",
                inline=False
            )

            for i, t in enumerate(page_trainees):
                rank = page_start + i + 1
                try:
                    member = interaction.guild.get_member(t["user_id"])
                    name = member.display_name if member else f"User {t['user_id']}"
                except Exception:
                    name = f"User {t['user_id']}"
                pct = get_completion_pct(t)
                bar = progress_bar(pct, 100, 8)
                cert_icon = "🏆" if t["certified"] else ("🎓" if t["exam_status"] == "passed" else "")
                cat = t["current_category"]
                cat_label = CATEGORIES.get(cat, "Complete")
                embed.add_field(
                    name=f"#{rank} {cert_icon} {name}",
                    value=f"`{bar}` {pct}% | Cat: {cat_label} | Exam: {t['exam_status'].title()} ({t['exam_score']}%) | Last: {t['last_active'][:10]}",
                    inline=False
                )

            embed.set_footer(text=f"Page {page_num}/{total_pages} | Sorted by completion % | Use /progress user:<member> for detail")
            pages.append(embed)

        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0], ephemeral=True)
        else:
            await interaction.response.send_message(embed=pages[0], view=ProgressView(pages), ephemeral=True)

    # Register the training group with the bot tree
    bot.tree.add_command(training_group)
    print("[TRAINING] ✅ Training commands registered")
