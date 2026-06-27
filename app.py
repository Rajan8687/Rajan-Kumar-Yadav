import math
import os
import re
import smtplib
import ssl
from datetime import datetime
from functools import wraps
from email.message import EmailMessage

from flask import Flask, abort, current_app, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _database_uri() -> str:
    uri = os.getenv("DATABASE_URL", "sqlite:///blog.db")
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


# app = Flask(__name__)
import tempfile

app = Flask(
    __name__,
    instance_path=tempfile.gettempdir(),
    instance_relative_config=False,
)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
    SQLALCHEMY_DATABASE_URI=_database_uri(),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
app.config["PROFILE_PIC_FOLDER"] = os.path.join(app.static_folder, "uploads", "profile_pics")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)

if not os.getenv("VERCEL"):
    os.makedirs(app.config["PROFILE_PIC_FOLDER"], exist_ok=True)


DEFAULT_PROFILE = {
    "name": "Rajan Kumar Yadav",
    "role": "DATA SCIENCE | MACHINE LEARNING ENGINEERING | MLOPS",
    "tagline": "Building scalable AI systems from data to deployment.",
    "email": "yadavrajan8687@gmail.com",
    "university": "CMR University, Bangalore",
    "github": "https://github.com/Rajan8687",
    "linkedin": "https://www.linkedin.com/in/rajan8687",
    "facebook": "https://www.facebook.com/adhakari.rajan.9",
    "instagram": "https://www.instagram.com/adhikari_rajan86/?hl=en",
    "location": "Bangalore, India",
    "live_project": "https://rajan-kumar-yadav.vercel.app/",
    "resume": "resume.pdf",
}

PROFILE_FIELDS = list(DEFAULT_PROFILE.keys())
AUTH_FIELDS = ("username", "email")

FOCUS_AREAS = [
    {
        "title": "Data science",
        "detail": "Turning raw datasets into useful patterns, dashboards, and decisions.",
    },
    {
        "title": "Machine learning",
        "detail": "Building simple models first, then measuring and improving them carefully.",
    },
    {
        "title": "MLOps engineering",
        "detail": "Packaging models, automating workflows, and keeping deployments reliable.",
    },
]

SKILLS = [
    "Python",
    "SQL",
    "Pandas",
    "NumPy",
    "Statistics",
    "Data Cleaning",
    "EDA",
    "Feature Engineering",
    "Machine Learning",
    "Scikit-learn",
    "TensorFlow",
    "Model Evaluation",
    "MLOps",
    "Docker",
    "Git & GitHub",
    "Flask",
    "Data Visualization",
    "Streamlit",
    "Tailwind CSS",
]

HIGHLIGHTS = [
    {"value": "1", "label": "portfolio project"},
    {"value": "1", "label": "resume download"},
    {"value": "100%", "label": "responsive design"},
]

SOCIAL_LINKS = [
    {"label": "GitHub", "href": DEFAULT_PROFILE["github"]},
    {"label": "LinkedIn", "href": DEFAULT_PROFILE["linkedin"]},
    {"label": "Facebook", "href": DEFAULT_PROFILE["facebook"]},
    {"label": "Instagram", "href": DEFAULT_PROFILE["instagram"]},
]

ALLOWED_PROFILE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

CAPSTONE_PROJECT = {
    "title": "Capstone Project",
    "slug": "capstone-project",
    "category": "Capstone",
    "excerpt": "My main data science project focused on building a practical AI workflow from data handling to deployment.",
    "featured": True,
    "content": """
<h2>Goal</h2>
<p>Build a full project that shows how data can move from raw collection to a useful deployed result.</p>
<h2>Approach</h2>
<p>Clean the dataset, explore patterns, design a model workflow, and present the result in a way that is easy to understand.</p>
<h2>Outcome</h2>
<p>A focused capstone example that reflects my work in data science, machine learning engineering, and MLOps.</p>

<h2>Links</h2>
<p><strong>GitHub Repository:</strong> <a href="https://github.com/Rajan8687/Capstone-Project" target="_blank">https://github.com/Rajan8687/Capstone-Project</a></p>
<p><strong>Live Website:</strong> <a href="https://capstone-project-x9p0.onrender.com/" target="_blank">https://capstone-project-x9p0.onrender.com/</a></p>
""".strip(),
}

PORTFOLIO_PROJECT = {
    "title": "Rajan Kumar Yadav Portfolio",
    "slug": "rajan-kumar-yadav-portfolio",
    "category": "Portfolio",
    "excerpt": "My personal portfolio website showcasing my projects, skills, and experience in Data Science, ML Engineering, and MLOps.",
    "featured": True,
    "content": """
<h2>Project Overview</h2>
<p>This is my personal portfolio website built to showcase my work and skills in Data Science, Machine Learning Engineering, and MLOps. The portfolio includes my projects, resume, blog articles, and contact information.</p>

<h2>Features</h2>
<ul>
<li>Project showcase with detailed descriptions</li>
<li>Blog section for technical articles</li>
<li>Responsive design for all devices</li>
<li>Contact form for professional inquiries</li>
<li>User authentication and dashboard for content management</li>
</ul>

<h2>Technologies Used</h2>
<ul>
<li>Python</li>
<li>Flask</li>
<li>SQLAlchemy</li>
<li>Tailwind CSS</li>
<li>HTML5</li>
<li>JavaScript</li>
</ul>

<h2>Links</h2>
<p><strong>GitHub Repository:</strong> <a href="https://github.com/Rajan8687/Rajan-Kumar-Yadav" target="_blank">https://github.com/Rajan8687/Rajan-Kumar-Yadav</a></p>
<p><strong>Live Website:</strong> <a href="https://rajan-kumar-yadav.vercel.app/" target="_blank">https://rajan-kumar-yadav.vercel.app/</a></p>
""".strip(),
}

# Rich featured-project metadata used by the homepage showcase cards.
# Each entry mirrors the DB Project plus extra display fields (icon, tags,
# highlights, github/live links) so the homepage can render a richer card.
FEATURED_PROJECTS = [
    {
        "title": PORTFOLIO_PROJECT["title"],
        "slug": PORTFOLIO_PROJECT["slug"],
        "category": PORTFOLIO_PROJECT["category"],
        "excerpt": PORTFOLIO_PROJECT["excerpt"],
        "icon": "layout-dashboard",
        "accent": "blue",
        "tags": ["Flask", "Python", "Tailwind CSS", "SQLAlchemy", "Responsive"],
        "highlights": [
            "Project showcase with detailed descriptions",
            "Blog with likes & comments",
            "Auth, dashboard & profile management",
            "Fully responsive dark/light UI",
        ],
        "github": "https://github.com/Rajan8687/Rajan-Kumar-Yadav",
        "live": "https://rajan-kumar-yadav.vercel.app/",
    },
    {
        "title": CAPSTONE_PROJECT["title"],
        "slug": CAPSTONE_PROJECT["slug"],
        "category": CAPSTONE_PROJECT["category"],
        "excerpt": CAPSTONE_PROJECT["excerpt"],
        "icon": "brain-circuit",
        "accent": "amber",
        "tags": ["Data Science", "Machine Learning", "MLOps", "Deployment"],
        "highlights": [
            "End-to-end data pipeline",
            "EDA, modeling & evaluation",
            "Model packaging & automation",
            "Live deployment on Render",
        ],
        "github": "https://github.com/Rajan8687/Capstone-Project",
        "live": "https://capstone-project-x9p0.onrender.com/",
    },
]


class SiteProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(280), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    university = db.Column(db.String(200), nullable=False)
    github = db.Column(db.String(300), nullable=False)
    linkedin = db.Column(db.String(300), nullable=False)
    facebook = db.Column(db.String(300), nullable=False)
    instagram = db.Column(db.String(300), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    live_project = db.Column(db.String(300), nullable=False)
    resume = db.Column(db.String(300), nullable=False, default="resume.pdf")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General")
    excerpt = db.Column(db.String(280), nullable=False, default="")
    content = db.Column(db.Text, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=False, default="Blog")
    excerpt = db.Column(db.String(280), nullable=False, default="")
    content = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    views = db.Column(db.Integer, default=0, nullable=False)
    likes = db.Column(db.Integer, default=0, nullable=False)
    comments = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    author = db.relationship("User", backref=db.backref("articles", lazy=True))


class ArticleLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    article = db.relationship("Article", backref=db.backref("article_likes", lazy=True))
    user = db.relationship("User", backref=db.backref("article_likes", lazy=True))


class ArticleComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    article = db.relationship("Article", backref=db.backref("article_comments", lazy=True))
    user = db.relationship("User", backref=db.backref("article_comments", lazy=True))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("password_reset_tokens", lazy=True))


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def extract_title_from_content(content: str) -> str:
    if not content:
        return "Untitled Article"

    heading = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", content, flags=re.IGNORECASE | re.DOTALL)
    if heading:
        title = re.sub(r"<[^>]+>", "", heading.group(1)).strip()
        if title:
            return title[:200]

    text = re.sub(r"<[^>]+>", "", content or "")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "Untitled Article"

    first_line = text.split("\n", 1)[0].strip()
    first_sentence = first_line.split(".", 1)[0].strip()
    title = first_sentence or first_line
    return title[:200] if title else "Untitled Article"


def seed_defaults() -> None:
    if not SiteProfile.query.first():
        db.session.add(SiteProfile(**DEFAULT_PROFILE))

    # Upsert the two featured projects (Portfolio + Capstone) so they are
    # always available on the homepage and /projects page. Existing rows with
    # the same slug are updated in place; any other projects are left intact.
    for source in (PORTFOLIO_PROJECT, CAPSTONE_PROJECT):
        existing = Project.query.filter_by(slug=source["slug"]).first()
        if existing:
            existing.title = source["title"]
            existing.category = source["category"]
            existing.excerpt = source["excerpt"]
            existing.content = source["content"]
            existing.featured = source.get("featured", True)
        else:
            db.session.add(
                Project(
                    title=source["title"],
                    slug=source["slug"],
                    category=source["category"],
                    excerpt=source["excerpt"],
                    content=source["content"],
                    featured=source.get("featured", True),
                )
            )

    if not User.query.first():
        bootstrap_username = os.getenv("ADMIN_USERNAME", "admin")
        bootstrap_email = os.getenv("ADMIN_EMAIL", DEFAULT_PROFILE["email"])
        bootstrap_password = os.getenv("ADMIN_PASSWORD", "admin123")
        user = User(
            username=bootstrap_username,
            email=bootstrap_email,
            password_hash=generate_password_hash(bootstrap_password),
        )
        db.session.add(user)
    
    db.session.flush()

    for user in User.query.all():
        if not UserProfile.query.filter_by(user_id=user.id).first():
            db.session.add(UserProfile(user_id=user.id))

    db.session.commit()


def get_profile_dict() -> dict:
    profile = SiteProfile.query.first()
    if not profile:
        return DEFAULT_PROFILE.copy()
    return {
        "name": profile.name,
        "role": profile.role,
        "tagline": profile.tagline,
        "email": profile.email,
        "university": profile.university,
        "github": profile.github,
        "linkedin": profile.linkedin,
        "facebook": profile.facebook,
        "instagram": profile.instagram,
        "location": profile.location,
        "live_project": profile.live_project,
        "resume": profile.resume,
    }


def get_user_profile(user: User | None = None, create: bool = False) -> UserProfile | None:
    user = user or get_current_user()
    if not user:
        return None

    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if profile is None and create:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


def ensure_article_author_column() -> None:
    inspector = inspect(db.engine)
    if "article" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("article")]
    if "author_id" in existing_columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE article ADD COLUMN author_id INTEGER"))


def ensure_user_profile_full_name_column() -> None:
    inspector = inspect(db.engine)
    if "user_profile" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("user_profile")]
    if "full_name" in existing_columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE user_profile ADD COLUMN full_name VARCHAR(150)"))


def ensure_article_metrics_columns() -> None:
    inspector = inspect(db.engine)
    if "article" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("article")]
    with db.engine.begin() as connection:
        if "views" not in existing_columns:
            connection.execute(text("ALTER TABLE article ADD COLUMN views INTEGER DEFAULT 0 NOT NULL"))
        if "likes" not in existing_columns:
            connection.execute(text("ALTER TABLE article ADD COLUMN likes INTEGER DEFAULT 0 NOT NULL"))
        if "comments" not in existing_columns:
            connection.execute(text("ALTER TABLE article ADD COLUMN comments INTEGER DEFAULT 0 NOT NULL"))


def ensure_site_profile_resume_column() -> None:
    inspector = inspect(db.engine)
    if "site_profile" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("site_profile")]
    if "resume" in existing_columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE site_profile ADD COLUMN resume VARCHAR(300) DEFAULT 'resume.pdf' NOT NULL"))


def get_admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "admin123")


def _smtp_settings() -> dict:
    host = os.getenv("MAIL_SERVER", "").strip()
    port = int(os.getenv("MAIL_PORT", "0") or 0)
    username = os.getenv("MAIL_USERNAME", "").strip()
    password = os.getenv("MAIL_PASSWORD", "")
    sender = os.getenv("MAIL_FROM", username).strip()
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
    use_ssl = os.getenv("MAIL_USE_SSL", "false").lower() in {"1", "true", "yes", "on"}

    if not host and username:
        domain = username.split("@")[-1].lower()
        if domain in {"gmail.com", "googlemail.com"}:
            host = "smtp.gmail.com"
            port = port or 587
            use_tls = True
        elif domain in {"outlook.com", "hotmail.com", "live.com", "msn.com"}:
            host = "smtp.office365.com"
            port = port or 587
            use_tls = True

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender": sender,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
    }


def send_contact_email(name: str, email: str, message: str) -> None:
    settings = _smtp_settings()
    if not settings["host"] or not settings["port"] or not settings["sender"]:
        raise RuntimeError("Mail server settings are not configured.")

    owner_email = get_profile_dict()["email"]
    subject = f"New contact form message from {name}"

    body = (
        f"You received a new message from your portfolio contact form.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n"
    )

    mail = EmailMessage()
    mail["Subject"] = subject
    mail["From"] = settings["sender"]
    mail["To"] = owner_email
    mail["Reply-To"] = email
    mail.set_content(body)

    context = ssl.create_default_context()
    if settings["use_ssl"]:
        with smtplib.SMTP_SSL(settings["host"], settings["port"], context=context) as smtp:
            if settings["username"]:
                smtp.login(settings["username"], settings["password"])
            smtp.send_message(mail)
        return

    with smtplib.SMTP(settings["host"], settings["port"]) as smtp:
        if settings["use_tls"]:
            smtp.starttls(context=context)
        if settings["username"]:
            smtp.login(settings["username"], settings["password"])
        smtp.send_message(mail)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def is_allowed_profile_image(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_PROFILE_IMAGE_EXTENSIONS


def save_profile_image(uploaded_file, user_id: int) -> str | None:
    original_name = secure_filename(uploaded_file.filename)
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()
    if ext not in ALLOWED_PROFILE_IMAGE_EXTENSIONS:
        return None

    filename = f"user_{user_id}_{int(datetime.utcnow().timestamp())}{ext}"
    relative_path = os.path.join("uploads", "profile_pics", filename).replace("\\", "/")
    full_path = os.path.join(app.static_folder, relative_path)
    uploaded_file.save(full_path)
    return relative_path


def cleanup_orphan_articles() -> None:
    orphaned_articles = Article.query.filter(Article.author_id.isnot(None)).filter(~Article.author.has()).all()
    if not orphaned_articles:
        return

    for article in orphaned_articles:
        db.session.delete(article)
    db.session.commit()


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapper


with app.app_context():
    db.create_all()
    ensure_article_author_column()
    ensure_article_metrics_columns()
    ensure_user_profile_full_name_column()
    ensure_site_profile_resume_column()
    seed_defaults()
    cleanup_orphan_articles()


@app.template_filter("reading_time")
def reading_time(text: str) -> int:
    words = len((text or "").split())
    return max(1, math.ceil(words / 180))


@app.context_processor
def inject_globals():
    current_user = get_current_user()
    return {
        "current_year": datetime.utcnow().year,
        "profile": get_profile_dict(),
        "current_user": current_user,
        "current_user_profile": get_user_profile(current_user) if current_user else None,
        "focus_areas": FOCUS_AREAS,
        "skills": SKILLS,
        "highlights": HIGHLIGHTS,
        "social_links": SOCIAL_LINKS,
        "featured_projects": FEATURED_PROJECTS,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resume")
def resume_download():
    profile = get_profile_dict()
    resume_path_stored = profile.get("resume", "resume.pdf")
    # Extract just the filename, handling both "resume.pdf" and "/static/resume.pdf"
    import os
    resume_filename = os.path.basename(resume_path_stored)
    resume_path = os.path.join(current_app.root_path, "static", resume_filename)
    return send_file(resume_path, as_attachment=True, download_name="Rajan_Kumar_Yadav_Resume.pdf", mimetype="application/pdf")


@app.route("/projects")
def projects():
    projects = Project.query.order_by(Project.featured.desc(), Project.created_at.desc()).all()
    return render_template("projects.html", projects=projects)


@app.route("/project/<slug>")
def project(slug):
    article = Project.query.filter_by(slug=slug).first_or_404()
    # Attach rich metadata (github/live links, tags, icon) from FEATURED_PROJECTS
    # when available so the detail page can render project-specific action buttons.
    featured = next((p for p in FEATURED_PROJECTS if p["slug"] == slug), None)
    return render_template("project.html", project=article, featured=featured)


@app.route("/blog")
def blog():
    cleanup_orphan_articles()
    articles = Article.query.filter_by(published=True).order_by(Article.created_at.desc()).all()
    return render_template("blog.html", articles=articles)


@app.route("/articles")
def articles():
    return redirect(url_for("blog"))


@app.route("/article/<slug>")
def article(slug):
    post = Article.query.filter_by(slug=slug).first_or_404()
    if not post.published and get_current_user() is None:
        abort(404)
    # Allow callers to request the article page without incrementing view counters
    skip_views = str(request.args.get("skip_views", "")).lower() in {"1", "true", "yes"}
    if not skip_views:
        post.views = (post.views or 0) + 1
        db.session.commit()
    comments = ArticleComment.query.filter_by(article_id=post.id).order_by(ArticleComment.created_at.desc()).all()
    return render_template("article.html", article=post, comments=comments)


@app.route("/article/<slug>/check-like", methods=["GET"])
def check_like(slug):
    post = Article.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    is_liked = False
    if current_user:
        is_liked = bool(ArticleLike.query.filter_by(article_id=post.id, user_id=current_user.id).first())
    else:
        liked_slugs = session.get("liked_articles", [])
        is_liked = slug in liked_slugs
    return jsonify({"is_liked": is_liked})


@app.route("/article/<slug>/like", methods=["POST"])
def like_article(slug):
    post = Article.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    # Toggle like/unlike so each user (or guest session) can only have one active like.
    if current_user:
        existing_like = ArticleLike.query.filter_by(article_id=post.id, user_id=current_user.id).first()
        if existing_like:
            db.session.delete(existing_like)
            post.likes = max(0, (post.likes or 0) - 1)
            db.session.commit()
            if is_ajax:
                return jsonify({"status": "unliked", "likes": post.likes})
            flash("Your like has been removed.", "info")
            return redirect(url_for("article", slug=slug, skip_views=1))
        like = ArticleLike(article_id=post.id, user_id=current_user.id)
        db.session.add(like)
    else:
        liked_slugs = session.get("liked_articles", [])
        if slug in liked_slugs:
            # Unlike for guest: remove from session and decrement
            liked_slugs = [s for s in liked_slugs if s != slug]
            session["liked_articles"] = liked_slugs
            post.likes = max(0, (post.likes or 0) - 1)
            db.session.commit()
            if is_ajax:
                return jsonify({"status": "unliked", "likes": post.likes})
            flash("Your like has been removed.", "info")
            return redirect(url_for("article", slug=slug, skip_views=1))
        liked_slugs.append(slug)
        session["liked_articles"] = liked_slugs

    post.likes = (post.likes or 0) + 1
    db.session.commit()
    if is_ajax:
        return jsonify({"status": "liked", "likes": post.likes})
    flash("Thanks for liking this article.", "success")
    # Redirect back to the article without incrementing views
    return redirect(url_for("article", slug=slug, skip_views=1))


@app.route("/article/<slug>/comment", methods=["POST"])
def comment_article(slug):
    post = Article.query.filter_by(slug=slug).first_or_404()
    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        flash("Please enter a comment before posting.", "danger")
        return redirect(url_for("article", slug=slug))

    current_user = get_current_user()
    comment = ArticleComment(
        article_id=post.id,
        user_id=current_user.id if current_user else None,
        text=comment_text,
    )
    db.session.add(comment)
    post.comments = (post.comments or 0) + 1
    db.session.commit()

    # If the commenter was anonymous, remember this comment id in session so the guest
    # can edit/delete it during the same session.
    if current_user is None:
        guest_ids = session.get("guest_comment_ids", [])
        guest_ids.append(comment.id)
        session["guest_comment_ids"] = guest_ids

    flash("Your comment has been posted.", "success")
    return redirect(url_for("article", slug=slug))


@app.route("/article/<slug>/comment/<int:comment_id>/edit", methods=["POST"])
def edit_comment(slug, comment_id):
    post = Article.query.filter_by(slug=slug).first_or_404()
    comment = ArticleComment.query.get_or_404(comment_id)
    current_user = get_current_user()

    allowed = False
    if current_user and comment.user_id == current_user.id:
        allowed = True
    else:
        guest_ids = session.get("guest_comment_ids", [])
        if comment.id in guest_ids:
            allowed = True

    if not allowed:
        flash("You cannot edit this comment.", "danger")
        return redirect(url_for("article", slug=slug))

    new_text = request.form.get("comment", "").strip()
    if not new_text:
        flash("Please enter a comment before updating.", "danger")
        return redirect(url_for("article", slug=slug))

    comment.text = new_text
    db.session.commit()
    flash("Comment updated.", "success")
    return redirect(url_for("article", slug=slug))


@app.route("/article/<slug>/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(slug, comment_id):
    post = Article.query.filter_by(slug=slug).first_or_404()
    comment = ArticleComment.query.get_or_404(comment_id)
    current_user = get_current_user()

    allowed = False
    if current_user and comment.user_id == current_user.id:
        allowed = True
    else:
        guest_ids = session.get("guest_comment_ids", [])
        if comment.id in guest_ids:
            allowed = True

    if not allowed:
        flash("You cannot delete this comment.", "danger")
        return redirect(url_for("article", slug=slug))

    # Remove guest ownership reference if present
    if comment.id in session.get("guest_comment_ids", []):
        guest_ids = [i for i in session.get("guest_comment_ids", []) if i != comment.id]
        session["guest_comment_ids"] = guest_ids

    db.session.delete(comment)
    post.comments = max(0, (post.comments or 0) - 1)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("article", slug=slug))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("contact"))

        db.session.add(Message(name=name, email=email, message=message))
        db.session.commit()
        try:
            send_contact_email(name, email, message)
            flash("Thanks. Your message has been sent to email and saved.", "success")
        except Exception:
            app.logger.exception("Failed to send contact form email")
            flash("Thanks. Your message was saved, but email delivery is not configured yet.", "danger")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            or_(db.func.lower(User.username) == identifier, db.func.lower(User.email) == identifier)
        ).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("You are now logged in.", "success")
            return redirect(url_for("dashboard"))

        flash("Incorrect username/email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        profile_picture = request.files.get("profile_picture")
        if profile_picture and profile_picture.filename:
            if not is_allowed_profile_image(profile_picture.filename):
                flash("Please upload a JPG, PNG, GIF, or WebP image.", "danger")
                return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        user_profile = UserProfile(user_id=user.id)
        if profile_picture and profile_picture.filename:
            image_path = save_profile_image(profile_picture, user.id)
            if image_path:
                user_profile.profile_image = image_path

        db.session.add(user_profile)
        db.session.commit()
        session["user_id"] = user.id
        flash("Account created. You are now logged in.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("Please enter your email address.", "danger")
            return redirect(url_for("forgot_password"))
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a unique token
            import secrets
            import string
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            
            # Delete any existing tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).delete()
            
            # Create new token that expires in 1 hour
            expires_at = datetime.utcnow() + datetime.timedelta(hours=1)
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at,
                used=False
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # Send email with reset link
            try:
                settings = _smtp_settings()
                if settings["host"] and settings["port"] and settings["sender"]:
                    reset_link = url_for("reset_password", token=token, _external=True)
                    
                    owner_email = get_profile_dict()["email"]
                    subject = f"Password Reset Request for {owner_email}"
                    
                    body = (
                        f"You requested a password reset for your account.\n\n"
                        f"Click the link below to reset your password:\n"
                        f"{reset_link}\n\n"
                        f"This link will expire in 1 hour.\n\n"
                        f"If you didn't request this, please ignore this email."
                    )
                    
                    mail = EmailMessage()
                    mail["Subject"] = subject
                    mail["From"] = settings["sender"]
                    mail["To"] = user.email
                    mail.set_content(body)
                    
                    context = ssl.create_default_context()
                    if settings["use_ssl"]:
                        with smtplib.SMTP_SSL(settings["host"], settings["port"], context=context) as smtp:
                            if settings["username"]:
                                smtp.login(settings["username"], settings["password"])
                            smtp.send_message(mail)
                    else:
                        with smtplib.SMTP(settings["host"], settings["port"]) as smtp:
                            if settings["use_tls"]:
                                smtp.starttls(context=context)
                            if settings["username"]:
                                smtp.login(settings["username"], settings["password"])
                            smtp.send_message(mail)
                    
                    flash("Password reset link has been sent to your email.", "success")
                else:
                    flash("Email is not configured. Please contact the administrator directly at " + get_profile_dict()["email"] + " to reset your password.", "warning")
            except Exception as e:
                app.logger.exception(f"Failed to send password reset email: {e}")
                flash("Failed to send email. Please contact the administrator directly at " + get_profile_dict()["email"] + " to reset your password.", "danger")
        else:
            # Always show success message to prevent email enumeration
            flash("If this email exists in our system, a password reset link has been sent.", "success")
        
        return redirect(url_for("forgot_password"))
    
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    
    if not reset_token:
        flash("Invalid or expired password reset link.", "danger")
        return redirect(url_for("forgot_password"))
    
    if reset_token.expires_at < datetime.utcnow():
        flash("Password reset link has expired.", "danger")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not new_password or not confirm_password:
            flash("Please fill in both password fields.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        # Update user password
        user = reset_token.user
        user.password_hash = generate_password_hash(new_password)
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        flash("Your password has been reset. You can now log in with your new password.", "success")
        return redirect(url_for("login"))
    
    return render_template("reset_password.html", token=token)


@app.route("/dashboard")
@login_required
def dashboard():
    current_user = get_current_user()
    articles = Article.query.filter_by(author_id=current_user.id).order_by(Article.created_at.desc()).all()
    return render_template("dashboard.html", articles=articles, article_to_edit=None)


@app.route("/profile")
@login_required
def profile():
    current_user = get_current_user()
    current_user_profile = get_user_profile(current_user, create=True)
    return render_template("profile.html", current_user_profile=current_user_profile)


@app.route("/dashboard/profile", methods=["POST"])
@login_required
def update_profile():
    profile = SiteProfile.query.first()
    if not profile:
        profile = SiteProfile(**DEFAULT_PROFILE)
        db.session.add(profile)

    for field in PROFILE_FIELDS:
        if field in request.form:
            setattr(profile, field, request.form.get(field, "").strip())

    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/profile-picture", methods=["POST"])
@login_required
def upload_profile_picture():
    current_user = get_current_user()
    user_profile = get_user_profile(current_user, create=True)
    uploaded_file = request.files.get("profile_picture")

    if uploaded_file is None or not uploaded_file.filename:
        flash("Please choose a profile picture to upload.", "danger")
        return redirect(url_for("dashboard"))

    original_name = secure_filename(uploaded_file.filename)
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()
    if ext not in ALLOWED_PROFILE_IMAGE_EXTENSIONS:
        flash("Please upload a JPG, PNG, GIF, or WebP image.", "danger")
        return redirect(url_for("dashboard"))

    filename = f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
    relative_path = os.path.join("uploads", "profile_pics", filename).replace("\\", "/")
    full_path = os.path.join(app.static_folder, relative_path)

    if user_profile.profile_image:
        old_path = os.path.join(app.static_folder, user_profile.profile_image)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                app.logger.warning("Unable to remove old profile image: %s", old_path)

    uploaded_file.save(full_path)
    user_profile.profile_image = relative_path
    db.session.commit()
    flash("Profile picture updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/profile/change-username", methods=["POST"])
@login_required
def change_username():
    current_user = get_current_user()
    new_username = request.form.get("new_username", "").strip()

    if not new_username:
        flash("Please provide a new username.", "danger")
        return redirect(url_for("profile"))

    existing_user = User.query.filter(db.func.lower(User.username) == new_username.lower()).first()
    if existing_user and existing_user.id != current_user.id:
        flash("That username is already taken.", "danger")
        return redirect(url_for("profile"))

    current_user.username = new_username
    db.session.commit()
    flash("Username updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/change-fullname", methods=["POST"])
@login_required
def change_fullname():
    current_user = get_current_user()
    user_profile = get_user_profile(current_user, create=True)
    new_full_name = request.form.get("new_full_name", "").strip()

    if not new_full_name:
        flash("Please provide your full name.", "danger")
        return redirect(url_for("profile"))

    user_profile.full_name = new_full_name
    db.session.commit()
    flash("Full name updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/change-email", methods=["POST"])
@login_required
def change_email():
    current_user = get_current_user()
    new_email = request.form.get("new_email", "").strip().lower()

    if not new_email or "@" not in new_email:
        flash("Please provide a valid email address.", "danger")
        return redirect(url_for("profile"))

    existing_user = User.query.filter(db.func.lower(User.email) == new_email.lower()).first()
    if existing_user and existing_user.id != current_user.id:
        flash("That email is already in use.", "danger")
        return redirect(url_for("profile"))

    current_user.email = new_email
    db.session.commit()
    flash("Email updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_user = get_current_user()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("Please fill in all password fields.", "danger")
        return redirect(url_for("profile"))

    if not check_password_hash(current_user.password_hash, current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(url_for("profile"))

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/update-all", methods=["POST"])
@login_required
def update_profile_settings():
    current_user = get_current_user()
    user_profile = get_user_profile(current_user, create=True)

    new_full_name = request.form.get("new_full_name", "").strip()
    new_email = request.form.get("new_email", "").strip().lower()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    updated = False
    password_validated = False

    if new_full_name and new_full_name != (user_profile.full_name or ""):
        user_profile.full_name = new_full_name
        updated = True

    if new_email and new_email != current_user.email:
        if "@" not in new_email:
            flash("Please provide a valid email address.", "danger")
            return redirect(url_for("profile"))

        existing_user = User.query.filter(db.func.lower(User.email) == new_email.lower()).first()
        if existing_user and existing_user.id != current_user.id:
            flash("That email is already in use.", "danger")
            return redirect(url_for("profile"))

        if not current_password:
            flash("Please enter your current password to change your email.", "danger")
            return redirect(url_for("profile"))

        if not check_password_hash(current_user.password_hash, current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("profile"))

        current_user.email = new_email
        updated = True
        password_validated = True

    if new_password or confirm_password:
        if not new_password or not confirm_password:
            flash("Please fill in both new password fields.", "danger")
            return redirect(url_for("profile"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("profile"))

        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "danger")
            return redirect(url_for("profile"))

        if not current_password:
            flash("Please enter your current password to change your password.", "danger")
            return redirect(url_for("profile"))

        if not password_validated and not check_password_hash(current_user.password_hash, current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("profile"))

        current_user.password_hash = generate_password_hash(new_password)
        updated = True

    if not updated:
        flash("No changes were made.", "danger")
        return redirect(url_for("profile"))

    db.session.commit()
    flash("All settings updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/delete-account", methods=["POST"])
@login_required
def delete_account():
    current_user = get_current_user()
    password = request.form.get("password", "")

    if not password:
        flash("Please enter your password to delete the account.", "danger")
        return redirect(url_for("profile"))

    if not check_password_hash(current_user.password_hash, password):
        flash("Password is incorrect.", "danger")
        return redirect(url_for("profile"))

    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    Article.query.filter_by(author_id=current_user.id).delete(synchronize_session=False)

    if user_profile:
        if user_profile.profile_image:
            image_path = os.path.join(app.static_folder, user_profile.profile_image)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    app.logger.warning("Unable to remove profile image during account deletion: %s", image_path)
        db.session.delete(user_profile)

    db.session.delete(current_user)
    db.session.commit()
    session.pop("user_id", None)
    flash("Your account has been deleted.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard/articles", methods=["POST"])
@login_required
def create_article():
    current_user = get_current_user()
    category = request.form.get("category", "").strip() or "Blog"
    excerpt = request.form.get("excerpt", "").strip()
    content = request.form.get("content", "").strip()
    published = request.form.get("published") == "on"

    if not content:
        flash("Content is required.", "danger")
        return redirect(url_for("dashboard"))

    title = extract_title_from_content(content)
    slug_value = slugify(title)
    if not slug_value:
        slug_value = f"article-{int(datetime.utcnow().timestamp())}"

    counter = 1
    unique_slug = slug_value
    while Article.query.filter_by(slug=unique_slug).first():
        counter += 1
        unique_slug = f"{slug_value}-{counter}"

    if not excerpt:
        excerpt = re.sub(r"<[^>]+>", "", content)[:180].replace("\n", " ").strip()

    db.session.add(
        Article(
            title=title,
            slug=unique_slug,
            category=category,
            excerpt=excerpt,
            content=content,
            published=published,
            author_id=current_user.id,
        )
    )
    db.session.commit()
    flash("Article created.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/articles/<int:article_id>/edit", methods=["GET", "POST"])
@login_required
def edit_article(article_id):
    current_user = get_current_user()
    article = Article.query.get_or_404(article_id)

    if article.author_id is not None and article.author_id != current_user.id:
        abort(403)

    if article.author_id is None:
        article.author_id = current_user.id

    if request.method == "POST":
        category = request.form.get("category", "").strip() or "Blog"
        excerpt = request.form.get("excerpt", "").strip()
        content = request.form.get("content", "").strip()
        published = request.form.get("published") == "on"

        if not content:
            flash("Content is required.", "danger")
            return redirect(url_for("edit_article", article_id=article_id))

        title = extract_title_from_content(content)
        slug_value = slugify(title) or article.slug
        if not slug_value:
            slug_value = f"article-{article.id}"

        conflict = Article.query.filter_by(slug=slug_value).first()
        if conflict and conflict.id != article.id:
            suffix = 1
            unique_slug = slug_value
            while conflict and conflict.id != article.id:
                suffix += 1
                unique_slug = f"{slug_value}-{suffix}"
                conflict = Article.query.filter_by(slug=unique_slug).first()
            slug_value = unique_slug

        if not excerpt:
            excerpt = re.sub(r"<[^>]+>", "", content)[:180].replace("\n", " ").strip()

        article.title = title
        article.slug = slug_value
        article.category = category
        article.excerpt = excerpt
        article.content = content
        article.published = published
        db.session.commit()
        flash("Article updated.", "success")
        return redirect(url_for("dashboard"))

    articles = Article.query.filter_by(author_id=current_user.id).order_by(Article.created_at.desc()).all()
    return render_template("dashboard.html", articles=articles, article_to_edit=article)


@app.route("/dashboard/articles/<int:article_id>/delete", methods=["POST"])
@login_required
def delete_article(article_id):
    current_user = get_current_user()
    article = Article.query.get_or_404(article_id)

    if article.author_id is not None and article.author_id != current_user.id:
        abort(403)

    # Delete related comments and likes first (cascade will handle this, but explicit is clearer)
    ArticleComment.query.filter_by(article_id=article_id).delete()
    ArticleLike.query.filter_by(article_id=article_id).delete()
    
    db.session.delete(article)
    db.session.commit()
    flash("Article deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin")
def admin_redirect():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
