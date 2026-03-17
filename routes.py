import random
import string
import time
from datetime import timedelta, datetime

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from werkzeug.security import check_password_hash, generate_password_hash
from parsers import *
from models import db, User, Event, EventRegistration, Announcement, Project, ProjectLike, ProjectComment, UserFollow

HTTP_200_OK           = 200
HTTP_201_CREATED      = 201
HTTP_400_BAD_REQUEST  = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_404_NOT_FOUND    = 404
HTTP_409_CONFLICT     = 409
HTTP_403_FORBIDDEN    = 403

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests as http_requests

GMAIL_ADDRESS  = "universitychlefclub@gmail.com"
GMAIL_APP_PASS = "rqki cvlk iqgr smdj"
CLUB_NAME      = "University Club Chlef"
LOGO_URL       = "https://images.cdn-files-a.com/uploads/1598328/800_5bd38322bcdfd.jpg"
OTP_EXPIRY_SEC = 120

VALID_GRADES = [
    'Student',
    'Professor',
    'Researcher',
    'Company manager',
]

VALID_DOMAINS = [
    'intelligence artificielle',
    'developpement web',
    'cyber securite',
    'reseaux et telecommunications',
    'systemes embarques',
    'science des donnees',
    'genie logiciel',
    'autre',
]

_pending_registrations = {}
_pending_resets        = {}


def send_follow_email(follower_firstname, follower_lastname, follower_image, to_email, to_name):
    greeting = f"Hello {to_name}," if to_name else "Hello,"
    follower_full = f"{follower_firstname} {follower_lastname}".strip()
    avatar_html = (
        f'<img src="{follower_image}" width="72" height="72" '
        f'style="border-radius:50%;border:3px solid #40916c;object-fit:cover;display:block;margin:0 auto 14px;"/>'
        if follower_image else
        f'<div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#2d6a4f,#40916c);'
        f'display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-size:28px;font-weight:700;'
        f'color:#fff;font-family:sans-serif;line-height:72px;text-align:center;">'
        f'{follower_firstname[0].upper() if follower_firstname else "?"}</div>'
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#f4f1ea;font-family:'Georgia',serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ea;padding:40px 16px;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#2d6a4f 0%,#1b4332 100%);padding:44px 48px;text-align:center;">
                <img src="{LOGO_URL}" width="76" height="76"
                     style="border-radius:16px;border:3px solid rgba(255,255,255,0.22);object-fit:cover;display:block;margin:0 auto 18px;"/>
                <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;font-family:'Georgia',serif;line-height:1.25;">
                  You have a new <span style="color:#d4a843;">follower!</span>
                </h1>
                <p style="margin:10px 0 0;color:rgba(255,255,255,0.6);font-family:sans-serif;font-size:13px;">{CLUB_NAME}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:48px;text-align:center;">
                <p style="font-family:sans-serif;font-size:15px;color:#666;margin:0 0 32px;">{greeting}</p>
                <div style="background:#f0f7f4;border:1.5px solid #b7dfc9;border-radius:18px;padding:32px 28px;margin:0 auto 32px;max-width:340px;">
                  {avatar_html}
                  <p style="margin:0 0 6px;font-family:sans-serif;font-size:19px;font-weight:700;color:#1b4332;">{follower_full}</p>
                  <div style="display:inline-block;background:rgba(45,106,79,0.1);border:1px solid rgba(45,106,79,0.25);border-radius:100px;padding:4px 16px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#2d6a4f;font-family:sans-serif;margin-top:4px;">is now following you</div>
                </div>
                <p style="font-family:sans-serif;font-size:14px;color:#777;line-height:1.75;margin:0 0 36px;">Your profile is growing! Check out <strong style="color:#2d6a4f;">{follower_full}</strong>'s profile and connect back on <strong style="color:#2d6a4f;">{CLUB_NAME}</strong>.</p>
                <p style="font-family:sans-serif;font-size:11px;color:#ccc;margin:0;">You received this because someone followed you on {CLUB_NAME}.</p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8f6f1;padding:24px 48px;text-align:center;border-top:1px solid #ede9df;">
                <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">&copy; 2026 {CLUB_NAME} &middot; University of Chlef, Algeria</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{CLUB_NAME} <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = f"{follower_full} started following you on {CLUB_NAME}!"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def send_invite_email(to_name, to_email):
    greeting = f"Dear {to_name}," if to_name else "Hello,"
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#f4f1ea;font-family:'Georgia',serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ea;padding:40px 16px;">
        <tr><td align="center">
          <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#2d6a4f 0%,#1b4332 100%);padding:48px;text-align:center;">
                <img src="{LOGO_URL}" width="90" height="90" style="border-radius:18px;border:3px solid rgba(255,255,255,0.25);object-fit:cover;display:block;margin:0 auto 20px;"/>
                <h1 style="margin:0;color:#ffffff;font-size:36px;font-weight:700;line-height:1.2;font-family:'Georgia',serif;">You're <span style="color:#d4a843;">Invited!</span></h1>
              </td>
            </tr>
            <tr>
              <td style="padding:48px;">
                <p style="font-family:sans-serif;font-size:15px;color:#555;margin:0 0 18px;">{greeting}</p>
                <p style="font-family:sans-serif;font-size:15px;color:#444;line-height:1.8;margin:0 0 36px;">We are thrilled to invite you to become part of <strong style="color:#2d6a4f;">{CLUB_NAME}</strong> — a vibrant community of students who collaborate, innovate, and grow together at the University of Chlef.</p>
                <p style="font-family:sans-serif;font-size:12px;color:#ccc;text-align:center;margin:0;">This invitation was personally sent by {CLUB_NAME}</p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8f6f1;padding:28px 48px;text-align:center;border-top:1px solid #ede9df;">
                <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">&copy; 2026 {CLUB_NAME} &middot; University of Chlef, Algeria</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{CLUB_NAME} <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = f"You're Invited to Join {CLUB_NAME}!"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def send_otp_email(to_email: str, otp: str):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#f4f1ea;font-family:'Georgia',serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ea;padding:40px 16px;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#2d6a4f 0%,#1b4332 100%);padding:44px 48px;text-align:center;">
                <img src="{LOGO_URL}" width="80" height="80" style="border-radius:16px;border:3px solid rgba(255,255,255,0.2);object-fit:cover;display:block;margin:0 auto 18px;"/>
                <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;font-family:'Georgia',serif;">Verify Your Identity</h1>
                <p style="margin:10px 0 0;color:rgba(255,255,255,0.6);font-family:sans-serif;font-size:13px;">{CLUB_NAME}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:48px;text-align:center;">
                <p style="font-family:sans-serif;font-size:15px;color:#555;margin:0 0 28px;line-height:1.7;">Use the code below to complete your verification.<br/>This code expires in <strong style="color:#2d6a4f;">{OTP_EXPIRY_SEC // 60} minutes</strong>.</p>
                <div style="background:#f0f7f4;border:2px dashed #40916c;border-radius:16px;padding:32px 24px;margin:0 0 28px;">
                  <p style="margin:0 0 16px;font-family:sans-serif;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:#999;text-align:center;">Your OTP Code</p>
                  <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>
                    {"".join(f'<td style="padding:0 4px;"><div style="width:50px;height:62px;background:#ffffff;border:2px solid #40916c;border-radius:10px;font-family:Courier New,monospace;font-size:30px;font-weight:700;color:#2d6a4f;text-align:center;line-height:62px;">{ch}</div></td>' for ch in otp)}
                  </tr></table>
                </div>
                <div style="background:#fff8e6;border:1px solid #f0c040;border-radius:10px;padding:12px 20px;margin-bottom:28px;">
                  <p style="margin:0;font-family:sans-serif;font-size:12px;color:#a07820;">&#9200; This code will expire in {OTP_EXPIRY_SEC // 60} minutes. Do not share it with anyone.</p>
                </div>
                <p style="font-family:sans-serif;font-size:12px;color:#ccc;margin:0;">If you didn't request this code, please ignore this email.</p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8f6f1;padding:24px 48px;text-align:center;border-top:1px solid #ede9df;">
                <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">&copy; 2026 {CLUB_NAME} &middot; University of Chlef, Algeria</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{CLUB_NAME} <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = f"Your OTP Code - {CLUB_NAME}"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def send_new_event_email(to_name: str, to_email: str, event):
    greeting  = f"Dear {to_name}," if to_name else "Hello,"
    start_fmt = event.start_at.strftime("%A, %B %d, %Y at %I:%M %p")
    end_fmt   = event.end_at.strftime("%A, %B %d, %Y at %I:%M %p") if event.end_at else "TBD"
    location  = event.location  if event.location  else "TBD"
    capacity  = f"{event.capacity} spots" if event.capacity else "Unlimited"
    etype     = event.event_type.capitalize() if event.event_type else "Other"
    desc_html = f'<p style="font-family:Arial,sans-serif;font-size:15px;color:#444;line-height:1.8;margin:0 0 28px;">{event.description}</p>' if event.description else ""
    img_html  = f'<img src="{event.image}" width="100%" style="display:block;max-height:260px;object-fit:cover;border-radius:12px;margin-bottom:28px;" alt="Event"/>' if event.image else ""

    html = (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'/></head>"
        "<body style='margin:0;padding:0;background:#f0ede6;'>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f0ede6;padding:36px 12px;'>"
        "<tr><td align='center'>"
        "<table width='560' cellpadding='0' cellspacing='0' style='background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 6px 32px rgba(0,0,0,0.09);'>"
        "<tr><td style='background:linear-gradient(135deg,#2d6a4f,#1b4332);padding:40px 44px 32px;text-align:center;'>"
        f"<img src='{LOGO_URL}' width='72' height='72' style='border-radius:14px;border:3px solid rgba(255,255,255,0.22);object-fit:cover;display:block;margin:0 auto 16px;'/>"
        f"<h1 style='margin:0;color:#ffffff;font-size:26px;font-weight:700;line-height:1.3;font-family:Georgia,serif;'>{event.title}</h1>"
        "</td></tr>"
        "<tr><td style='padding:36px 44px;'>"
        f"<p style='font-family:Arial,sans-serif;font-size:15px;color:#555;margin:0 0 14px;'>{greeting}</p>"
        + img_html + desc_html
        + "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f2f8f5;border-radius:12px;border:1px solid #d4eade;margin-bottom:28px;'>"
        f"<tr><td style='padding:14px 18px;border-bottom:1px solid #d4eade;'><span style='font-family:Arial,sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#888;'>Starts</span><br/><span style='font-family:Arial,sans-serif;font-size:14px;color:#1b4332;font-weight:700;'>&#128197; {start_fmt}</span></td></tr>"
        f"<tr><td style='padding:14px 18px;border-bottom:1px solid #d4eade;'><span style='font-family:Arial,sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#888;'>Ends</span><br/><span style='font-family:Arial,sans-serif;font-size:14px;color:#1b4332;font-weight:700;'>&#127937; {end_fmt}</span></td></tr>"
        f"<tr><td style='padding:14px 18px;border-bottom:1px solid #d4eade;'><span style='font-family:Arial,sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#888;'>Location</span><br/><span style='font-family:Arial,sans-serif;font-size:14px;color:#1b4332;font-weight:700;'>&#128205; {location}</span></td></tr>"
        f"<tr><td style='padding:14px 18px;'><span style='font-family:Arial,sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#888;'>Capacity</span><br/><span style='font-family:Arial,sans-serif;font-size:14px;color:#1b4332;font-weight:700;'>&#129681; {capacity}</span></td></tr>"
        "</table>"
        "</td></tr>"
        "<tr><td style='background:#f7f5f0;padding:22px 44px;text-align:center;border-top:1px solid #e8e4db;'>"
        f"<p style='font-family:Arial,sans-serif;font-size:11px;color:#bbb;margin:0;'>&copy; 2026 {CLUB_NAME} &middot; University of Chlef, Algeria</p>"
        "</td></tr></table></td></tr></table></body></html>"
    )
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{CLUB_NAME} <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = f"New Event: {event.title} - {CLUB_NAME}"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def send_reset_password_email(to_email: str, otp: str):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#f4f1ea;font-family:'Georgia',serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ea;padding:40px 16px;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#7b2d2d 0%,#4a1010 100%);padding:44px 48px;text-align:center;">
                <img src="{LOGO_URL}" width="80" height="80" style="border-radius:16px;border:3px solid rgba(255,255,255,0.2);object-fit:cover;display:block;margin:0 auto 18px;"/>
                <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;font-family:'Georgia',serif;">Reset Your Password</h1>
                <p style="margin:10px 0 0;color:rgba(255,255,255,0.6);font-family:sans-serif;font-size:13px;">{CLUB_NAME}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:48px;text-align:center;">
                <p style="font-family:sans-serif;font-size:15px;color:#555;margin:0 0 28px;line-height:1.7;">We received a request to reset your password.<br/>Use the code below — it expires in <strong style="color:#7b2d2d;">{OTP_EXPIRY_SEC // 60} minutes</strong>.</p>
                <div style="background:#fdf0f0;border:2px dashed #c0392b;border-radius:16px;padding:32px 24px;margin:0 0 28px;">
                  <p style="margin:0 0 16px;font-family:sans-serif;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:#999;text-align:center;">Your Reset Code</p>
                  <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>
                    {"".join(f'<td style="padding:0 4px;"><div style="width:50px;height:62px;background:#ffffff;border:2px solid #c0392b;border-radius:10px;font-family:Courier New,monospace;font-size:30px;font-weight:700;color:#7b2d2d;text-align:center;line-height:62px;">{ch}</div></td>' for ch in otp)}
                  </tr></table>
                </div>
                <p style="font-family:sans-serif;font-size:12px;color:#ccc;margin:0;">If you didn't request a password reset, no action is needed.</p>
              </td>
            </tr>
            <tr>
              <td style="background:#f8f6f1;padding:24px 48px;text-align:center;border-top:1px solid #ede9df;">
                <p style="font-family:sans-serif;font-size:11px;color:#bbb;margin:0;">&copy; 2026 {CLUB_NAME} &middot; University of Chlef, Algeria</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{CLUB_NAME} <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = f"Password Reset Code - {CLUB_NAME}"
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def _forgot_password(role):
    data  = request.json or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'error': 'email is required'}), HTTP_400_BAD_REQUEST
    user = User.query.filter_by(email=email).first()
    if not user or user.role != role:
        return jsonify({'message': 'If this email exists, an OTP has been sent'}), HTTP_200_OK
    otp = str(random.randint(100000, 999999))
    _pending_resets[email] = {'otp': otp, 'sent_at': time.time(), 'role': role}
    try:
        send_reset_password_email(email, otp)
    except Exception as e:
        _pending_resets.pop(email, None)
        return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500
    return jsonify({'message': 'If this email exists, an OTP has been sent'}), HTTP_200_OK


def _verify_reset_otp(role):
    data  = request.json or {}
    email = data.get('email', '').strip()
    otp   = data.get('otp', '').strip()
    if not email or not otp:
        return jsonify({'error': 'email and otp are required'}), HTTP_400_BAD_REQUEST
    pending = _pending_resets.get(email)
    if not pending or pending['role'] != role:
        return jsonify({'error': 'No pending reset for this email'}), HTTP_400_BAD_REQUEST
    if time.time() - pending['sent_at'] > OTP_EXPIRY_SEC:
        _pending_resets.pop(email, None)
        return jsonify({'error': 'OTP expired, please request a new one'}), HTTP_400_BAD_REQUEST
    if otp != pending['otp']:
        return jsonify({'error': 'Invalid OTP'}), HTTP_400_BAD_REQUEST
    _pending_resets[email]['verified'] = True
    return jsonify({'message': 'OTP verified', 'email': email}), HTTP_200_OK


def _reset_password(role):
    data         = request.json or {}
    email        = data.get('email', '').strip()
    new_password = data.get('new_password', '')
    if not email or not new_password:
        return jsonify({'error': 'email and new_password are required'}), HTTP_400_BAD_REQUEST
    if len(new_password) < 6:
        return jsonify({'error': 'Password is too short (min 6 characters)'}), HTTP_400_BAD_REQUEST
    pending = _pending_resets.get(email)
    if not pending or pending['role'] != role or not pending.get('verified'):
        return jsonify({'error': 'OTP not verified. Please complete verification first'}), HTTP_400_BAD_REQUEST
    user = User.query.filter_by(email=email).first()
    if not user or user.role != role:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    user.password = generate_password_hash(new_password)
    db.session.commit()
    _pending_resets.pop(email, None)
    return jsonify({'message': 'Password reset successfully'}), HTTP_200_OK


def _check_banned(user):
    if user and user.is_banned:
        return jsonify({'status': 'ban', 'reason': user.ban_reason}), HTTP_403_FORBIDDEN
    return None


auth = Blueprint("auth", __name__, url_prefix="/api/v1/")


def _register_user(role, data=None):
    if data is None:
        data = request.json or {}
    firstname = data.get('firstname', '').strip()
    lastname  = data.get('lastname', '').strip()
    email     = data.get('email', '').strip()
    phone     = data.get('phone', '').strip()
    password  = data.get('password', '')
    image     = data.get('image')
    grade     = data.get('grade', 'Admin' if role == 'Admin' else '').strip()
    domain    = data.get('domain', '').strip().lower()
    if not all([firstname, lastname, email, phone, password]):
        return jsonify({'error': 'All fields are required'}), HTTP_400_BAD_REQUEST
    if len(password) < 6:
        return jsonify({'error': 'Password is too short'}), HTTP_400_BAD_REQUEST
    if role == 'client':
        if not grade:
            return jsonify({'error': 'grade is required'}), HTTP_400_BAD_REQUEST
        if grade not in VALID_GRADES:
            return jsonify({'error': f'Invalid grade. Choose from: {", ".join(VALID_GRADES)}'}), HTTP_400_BAD_REQUEST
        if not domain:
            return jsonify({'error': 'domain is required'}), HTTP_400_BAD_REQUEST
        if domain not in VALID_DOMAINS:
            return jsonify({'error': f'Invalid domain. Choose from: {", ".join(VALID_DOMAINS)}'}), HTTP_400_BAD_REQUEST
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email is taken'}), HTTP_409_CONFLICT
    if User.query.filter_by(phone=phone).first() is not None:
        return jsonify({'error': 'Phone number is taken'}), HTTP_409_CONFLICT
    pwd_hash = generate_password_hash(password)
    identify = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    user = User(firstname=firstname, lastname=lastname, email=email, phone=phone,
                password=pwd_hash, image=image, identify=identify, role=role, grade=grade, domain=domain)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created', 'user': {'firstname': user.firstname, 'lastname': user.lastname, 'email': user.email, 'phone': user.phone, 'image': user.image, 'role': user.role, 'grade': user.grade, 'domain': user.domain}}), HTTP_201_CREATED


def _login_user(expected_role=None):
    data     = request.json or {}
    email    = data.get('email', '')
    password = data.get('password', '')
    user     = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        if expected_role and user.role != expected_role:
            return jsonify({'error': 'Wrong role for this endpoint'}), HTTP_401_UNAUTHORIZED
        ban_response = _check_banned(user)
        if ban_response:
            return ban_response
        refresh       = create_refresh_token(identity=user.identify)
        access_expiry = timedelta(days=30)
        access        = create_access_token(identity=user.identify, expires_delta=access_expiry)
        return jsonify({'user': {'refresh': refresh, 'access': access, 'access_expiry': access_expiry.total_seconds()}}), HTTP_200_OK
    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED


def _pre_register(role):
    data      = request.json or {}
    firstname = data.get('firstname', '').strip()
    lastname  = data.get('lastname', '').strip()
    email     = data.get('email', '').strip()
    phone     = data.get('phone', '').strip()
    password  = data.get('password', '')
    image     = data.get('image')
    grade     = data.get('grade', '').strip()
    domain    = data.get('domain', '').strip().lower()
    if not all([firstname, lastname, email, phone, password]):
        return jsonify({'error': 'All fields are required'}), HTTP_400_BAD_REQUEST
    if len(password) < 6:
        return jsonify({'error': 'Password is too short'}), HTTP_400_BAD_REQUEST
    if role == 'client':
        if not grade:
            return jsonify({'error': 'grade is required'}), HTTP_400_BAD_REQUEST
        if grade not in VALID_GRADES:
            return jsonify({'error': f'Invalid grade. Choose from: {", ".join(VALID_GRADES)}'}), HTTP_400_BAD_REQUEST
        if not domain:
            return jsonify({'error': 'domain is required'}), HTTP_400_BAD_REQUEST
        if domain not in VALID_DOMAINS:
            return jsonify({'error': f'Invalid domain. Choose from: {", ".join(VALID_DOMAINS)}'}), HTTP_400_BAD_REQUEST
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email is taken'}), HTTP_409_CONFLICT
    if User.query.filter_by(phone=phone).first() is not None:
        return jsonify({'error': 'Phone number is taken'}), HTTP_409_CONFLICT
    otp = str(random.randint(100000, 999999))
    _pending_registrations[email] = {'firstname': firstname, 'lastname': lastname, 'email': email, 'phone': phone, 'password': password, 'image': image, 'role': role, 'grade': grade, 'domain': domain, 'otp': otp, 'sent_at': time.time()}
    try:
        send_otp_email(email, otp)
    except Exception as e:
        return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500
    return jsonify({'message': 'OTP sent to email'}), HTTP_200_OK


def _verify_otp_and_create(role):
    data  = request.json or {}
    email = data.get('email', '').strip()
    otp   = data.get('otp', '').strip()
    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), HTTP_400_BAD_REQUEST
    pending = _pending_registrations.get(email)
    if not pending:
        return jsonify({'error': 'No pending registration for this email'}), HTTP_400_BAD_REQUEST
    if pending['role'] != role:
        return jsonify({'error': 'Role mismatch'}), HTTP_400_BAD_REQUEST
    if time.time() - pending['sent_at'] > OTP_EXPIRY_SEC:
        _pending_registrations.pop(email, None)
        return jsonify({'error': 'OTP expired, please register again'}), HTTP_400_BAD_REQUEST
    if otp != pending['otp']:
        return jsonify({'error': 'Invalid OTP'}), HTTP_400_BAD_REQUEST
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email is taken'}), HTTP_409_CONFLICT
    if User.query.filter_by(phone=pending['phone']).first() is not None:
        return jsonify({'error': 'Phone number is taken'}), HTTP_409_CONFLICT
    pwd_hash = generate_password_hash(pending['password'])
    identify = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    user = User(firstname=pending['firstname'], lastname=pending['lastname'], email=pending['email'], phone=pending['phone'], password=pwd_hash, image=pending['image'], identify=identify, role=pending['role'], grade=pending['grade'], domain=pending['domain'])
    db.session.add(user)
    db.session.commit()
    _pending_registrations.pop(email, None)
    return jsonify({'message': 'User created', 'user': {'firstname': user.firstname, 'lastname': user.lastname, 'email': user.email, 'phone': user.phone, 'image': user.image, 'role': user.role, 'grade': user.grade, 'domain': user.domain}}), HTTP_201_CREATED


@auth.post('/admin/register')
@cross_origin()
def admin_register():
    return _register_user('Admin')

@auth.post('/admin/login')
@cross_origin()
def admin_login():
    return _login_user('Admin')

@auth.post('/admin/pre-register')
@cross_origin()
def admin_pre_register():
    return _pre_register('Admin')

@auth.post('/admin/verify-otp')
@cross_origin()
def admin_verify_otp():
    return _verify_otp_and_create('Admin')

@auth.post('/client/register')
@cross_origin()
def client_register():
    return _register_user('client')

@auth.post('/client/login')
@cross_origin()
def client_login():
    return _login_user('client')

@auth.post('/client/pre-register')
@cross_origin()
def client_pre_register():
    return _pre_register('client')

@auth.post('/client/verify-otp')
@cross_origin()
def client_verify_otp():
    return _verify_otp_and_create('client')

@auth.post('/admin/forgot-password')
@cross_origin()
def admin_forgot_password():
    return _forgot_password('Admin')

@auth.post('/admin/verify-reset-otp')
@cross_origin()
def admin_verify_reset_otp():
    return _verify_reset_otp('Admin')

@auth.post('/admin/reset-password')
@cross_origin()
def admin_reset_password():
    return _reset_password('Admin')

@auth.post('/client/forgot-password')
@cross_origin()
def client_forgot_password():
    return _forgot_password('client')

@auth.post('/client/verify-reset-otp')
@cross_origin()
def client_verify_reset_otp():
    return _verify_reset_otp('client')

@auth.post('/client/reset-password')
@cross_origin()
def client_reset_password():
    return _reset_password('client')

@auth.get('/client/grades')
@cross_origin()
def get_grades():
    return jsonify({'grades': VALID_GRADES}), HTTP_200_OK

@auth.get('/client/domains')
@cross_origin()
def get_domains():
    return jsonify({'domains': VALID_DOMAINS}), HTTP_200_OK

@auth.get('/admin/fetch-all')
@jwt_required()
@cross_origin()
def admin_fetch_all():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    students = User.query.filter_by(role='client').all()
    return jsonify({'students': [{'firstname': s.firstname, 'lastname': s.lastname, 'email': s.email, 'phone': s.phone, 'image': s.image, 'grade': s.grade, 'domain': s.domain, 'identify': s.identify, 'is_banned': s.is_banned, 'ban_reason': s.ban_reason} for s in students]}), HTTP_200_OK

@auth.post('/admin/invite')
@jwt_required()
@cross_origin()
def admin_invite():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data     = request.json or {}
    to_name  = data.get('name')
    to_email = data.get('email')
    if not to_email:
        return jsonify({'error': 'Email is required'}), HTTP_400_BAD_REQUEST
    try:
        send_invite_email(to_name, to_email)
    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
    return jsonify({'message': f'Invitation sent to {to_email}'}), HTTP_200_OK

@auth.post('/admin/ban')
@jwt_required()
@cross_origin()
def admin_ban():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data     = request.json or {}
    identify = data.get('identify', '').strip()
    reason   = data.get('reason', '').strip()
    if not identify:
        return jsonify({'error': 'identify is required'}), HTTP_400_BAD_REQUEST
    if not reason:
        return jsonify({'error': 'reason is required'}), HTTP_400_BAD_REQUEST
    target = User.query.filter_by(identify=identify).first()
    if not target:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    if target.role == 'Admin':
        return jsonify({'error': 'Cannot ban an Admin'}), HTTP_400_BAD_REQUEST
    if target.is_banned:
        return jsonify({'error': 'User is already banned'}), HTTP_409_CONFLICT
    target.is_banned  = True
    target.ban_reason = reason
    db.session.commit()
    return jsonify({'message': f'{target.firstname} {target.lastname} has been banned', 'identify': target.identify, 'ban_reason': target.ban_reason}), HTTP_200_OK

@auth.post('/admin/unban')
@jwt_required()
@cross_origin()
def admin_unban():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data     = request.json or {}
    identify = data.get('identify', '').strip()
    if not identify:
        return jsonify({'error': 'identify is required'}), HTTP_400_BAD_REQUEST
    target = User.query.filter_by(identify=identify).first()
    if not target:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    if not target.is_banned:
        return jsonify({'error': 'User is not banned'}), HTTP_409_CONFLICT
    target.is_banned  = False
    target.ban_reason = None
    db.session.commit()
    return jsonify({'message': f'{target.firstname} {target.lastname} has been unbanned', 'identify': target.identify}), HTTP_200_OK

@auth.get('/me')
@jwt_required()
@cross_origin()
def me():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if user:
        ban_response = _check_banned(user)
        if ban_response:
            return ban_response
        return jsonify({'perm': user.role, 'id': user.id, 'firstname': user.firstname, 'lastname': user.lastname, 'email': user.email, 'phone': user.phone, 'image': user.image, 'grade': user.grade, 'domain': user.domain, 'created_at': user.created_at}), HTTP_200_OK
    return jsonify({'error': 'Invalid token'}), HTTP_404_NOT_FOUND

@auth.put('/me')
@jwt_required()
@cross_origin()
def update_me():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), HTTP_404_NOT_FOUND
    ban_response = _check_banned(user)
    if ban_response:
        return ban_response
    data = request.json or {}
    if 'phone' in data and data['phone'] != user.phone:
        if User.query.filter_by(phone=data['phone']).first() is not None:
            return jsonify({'error': 'Phone number is taken'}), HTTP_409_CONFLICT
    if 'password' in data:
        if len(data['password']) < 6:
            return jsonify({'error': 'Password is too short'}), HTTP_400_BAD_REQUEST
        user.password = generate_password_hash(data['password'])
    if 'grade' in data:
        grade = data['grade'].strip()
        if grade not in VALID_GRADES:
            return jsonify({'error': f'Invalid grade. Choose from: {", ".join(VALID_GRADES)}'}), HTTP_400_BAD_REQUEST
        user.grade = grade
    if 'domain' in data:
        domain = data['domain'].strip().lower()
        if domain not in VALID_DOMAINS:
            return jsonify({'error': f'Invalid domain. Choose from: {", ".join(VALID_DOMAINS)}'}), HTTP_400_BAD_REQUEST
        user.domain = domain
    for field in ('firstname', 'lastname', 'email', 'phone', 'image'):
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return jsonify({'message': 'User updated', 'user': {'firstname': user.firstname, 'lastname': user.lastname, 'email': user.email, 'phone': user.phone, 'image': user.image, 'role': user.role, 'grade': user.grade, 'domain': user.domain}}), HTTP_200_OK

@auth.get('/token/refresh')
@jwt_required(refresh=True)
@cross_origin()
def refresh_users_token():
    identity = get_jwt_identity()
    access   = create_access_token(identity=identity)
    return jsonify({'access': access}), HTTP_200_OK

@auth.get('/getinfo')
@cross_origin()
def get_info():
    html   = fetch(LIST_URL)
    parser = PostParser()
    parser.feed(html)
    return jsonify({"posts": parser.posts})


def _translate_chunk(chunk, target_lang):
    resp = http_requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": chunk},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(part[0] for part in data[0] if part[0])


def _google_translate(text, target_lang):
    if not text or not target_lang:
        return text
    max_len = 4500
    chunks  = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    chunks.append(text)
    return "\n".join(_translate_chunk(c, target_lang) for c in chunks)


@auth.get('/getsuperinfo/<int:post_id>')
@cross_origin()
def get_super_info(post_id):
    url = BASE_URL.format(id=post_id)
    try:
        html = fetch(url)
    except Exception:
        return jsonify({"error": "Post not found"}), 404
    parser = ArticleParser()
    parser.feed(html)
    raw_text = "\n".join(parser.paragraphs) if parser.paragraphs else None
    lang            = request.args.get("lang", "").strip()
    translate_error = None
    translated_text = raw_text
    if lang and raw_text:
        try:
            translated_text = _google_translate(raw_text, lang)
        except Exception as e:
            translate_error = str(e)
            translated_text = raw_text
    return jsonify({"id": post_id, "text": translated_text, "language": lang if lang else "original", "translate_error": translate_error, "pdf": parser.pdf_links if parser.pdf_links else None, "images": parser.images if parser.images else None})


@auth.post('/events')
@jwt_required()
@cross_origin()
def create_event():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data        = request.json or {}
    title       = data.get('title', '').strip()
    start_at    = data.get('start_at')
    description = data.get('description')
    location    = data.get('location')
    image       = data.get('image')
    end_at      = data.get('end_at')
    event_type  = data.get('event_type', 'other')
    capacity    = data.get('capacity')
    is_visible  = data.get('is_visible', True)
    if not title or not start_at:
        return jsonify({'error': 'title and start_at are required'}), HTTP_400_BAD_REQUEST
    try:
        start_at = datetime.fromisoformat(start_at)
        end_at   = datetime.fromisoformat(end_at) if end_at else None
    except ValueError:
        return jsonify({'error': 'Invalid date format, use ISO 8601'}), HTTP_400_BAD_REQUEST
    event = Event(title=title, description=description, location=location, image=image, start_at=start_at, end_at=end_at, event_type=event_type, capacity=capacity, is_visible=is_visible)
    db.session.add(event)
    db.session.commit()
    event_data = {'title': event.title, 'description': event.description, 'location': event.location, 'image': event.image, 'start_at': event.start_at, 'end_at': event.end_at, 'event_type': event.event_type, 'capacity': event.capacity}
    students = User.query.filter_by(role='client').with_entities(User.firstname, User.email).all()
    from flask import current_app
    import threading
    class _Snap:
        def __init__(self, d): self.__dict__.update(d)
    def _blast(app, users, data):
        with app.app_context():
            evt = _Snap(data)
            for firstname, email in users:
                try:
                    send_new_event_email(firstname, email, evt)
                except Exception as exc:
                    print(f"[event email] failed for {email}: {exc}")
    threading.Thread(target=_blast, args=(current_app._get_current_object(), students, event_data), daemon=False).start()
    return jsonify({'message': 'Event created', 'event': {'id': event.id, 'title': event.title, 'location': event.location, 'start_at': event.start_at.isoformat(), 'event_type': event.event_type, 'capacity': event.capacity}}), HTTP_201_CREATED


@auth.get('/events')
@jwt_required()
@cross_origin()
def get_events():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    events = Event.query.filter_by(is_visible=True).order_by(Event.start_at.asc()).all()
    return jsonify({'events': [{'id': e.id, 'title': e.title, 'description': e.description, 'location': e.location, 'image': e.image, 'start_at': e.start_at.isoformat(), 'end_at': e.end_at.isoformat() if e.end_at else None, 'event_type': e.event_type, 'capacity': e.capacity, 'registered_count': e.registered_count, 'is_full': e.is_full, 'is_registered': EventRegistration.query.filter_by(user_id=user.id, event_id=e.id).first() is not None} for e in events]}), HTTP_200_OK


@auth.post('/events/<int:event_id>/join')
@jwt_required()
@cross_origin()
def join_event(event_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    event = Event.query.get(event_id)
    if not event or not event.is_visible:
        return jsonify({'error': 'Event not found'}), HTTP_404_NOT_FOUND
    if event.is_full:
        return jsonify({'error': 'Event is full'}), HTTP_409_CONFLICT
    already = EventRegistration.query.filter_by(user_id=user.id, event_id=event.id).first()
    if already:
        return jsonify({'error': 'Already registered'}), HTTP_409_CONFLICT
    reg = EventRegistration(user_id=user.id, event_id=event.id)
    db.session.add(reg)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), HTTP_201_CREATED


@auth.delete('/events/<int:event_id>/quit')
@jwt_required()
@cross_origin()
def quit_event(event_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    event = Event.query.get(event_id)
    if not event or not event.is_visible:
        return jsonify({'error': 'Event not found'}), HTTP_404_NOT_FOUND
    reg = EventRegistration.query.filter_by(user_id=user.id, event_id=event.id).first()
    if not reg:
        return jsonify({'error': 'Not registered for this event'}), HTTP_404_NOT_FOUND
    db.session.delete(reg)
    db.session.commit()
    return jsonify({'message': 'Unregistered from event successfully'}), HTTP_200_OK


@auth.put('/events/<int:event_id>')
@jwt_required()
@cross_origin()
def edit_event(event_id):
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), HTTP_404_NOT_FOUND
    data = request.json or {}
    if 'title' in data: event.title = data['title'].strip()
    if 'description' in data: event.description = data['description']
    if 'location' in data: event.location = data['location']
    if 'image' in data: event.image = data['image']
    if 'event_type' in data: event.event_type = data['event_type']
    if 'capacity' in data: event.capacity = data['capacity']
    if 'is_visible' in data: event.is_visible = data['is_visible']
    if 'start_at' in data:
        try: event.start_at = datetime.fromisoformat(data['start_at'])
        except ValueError: return jsonify({'error': 'Invalid start_at format'}), HTTP_400_BAD_REQUEST
    if 'end_at' in data:
        try: event.end_at = datetime.fromisoformat(data['end_at']) if data['end_at'] else None
        except ValueError: return jsonify({'error': 'Invalid end_at format'}), HTTP_400_BAD_REQUEST
    db.session.commit()
    return jsonify({'message': 'Event updated', 'event': {'id': event.id, 'title': event.title, 'description': event.description, 'location': event.location, 'start_at': event.start_at.isoformat(), 'end_at': event.end_at.isoformat() if event.end_at else None, 'event_type': event.event_type, 'capacity': event.capacity, 'is_visible': event.is_visible}}), HTTP_200_OK


@auth.delete('/events/<int:event_id>')
@jwt_required()
@cross_origin()
def delete_event(event_id):
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), HTTP_404_NOT_FOUND
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted successfully'}), HTTP_200_OK


@auth.post('/announcements')
@jwt_required()
@cross_origin()
def create_announcement():
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data       = request.json or {}
    title      = data.get('title', '').strip()
    content    = data.get('content', '').strip()
    image      = data.get('image')
    is_pinned  = data.get('is_pinned', False)
    is_visible = data.get('is_visible', True)
    if not title or not content:
        return jsonify({'error': 'title and content are required'}), HTTP_400_BAD_REQUEST
    announcement = Announcement(title=title, content=content, image=image, is_pinned=is_pinned, is_visible=is_visible, author_id=admin.id)
    db.session.add(announcement)
    db.session.commit()
    return jsonify({'message': 'Announcement created', 'announcement': {'id': announcement.id, 'title': announcement.title, 'is_pinned': announcement.is_pinned, 'created_at': announcement.created_at.isoformat()}}), HTTP_201_CREATED


@auth.get('/announcements')
@jwt_required()
@cross_origin()
def get_announcements():
    user_id = get_jwt_identity()
    if not User.query.filter_by(identify=user_id).first():
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    announcements = Announcement.query.filter_by(is_visible=True).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return jsonify({'announcements': [{'id': a.id, 'title': a.title, 'content': a.content, 'image': a.image, 'is_pinned': a.is_pinned, 'created_at': a.created_at.isoformat(), 'author': {'firstname': a.author.firstname, 'lastname': a.author.lastname, 'image': a.author.image}} for a in announcements]}), HTTP_200_OK


@auth.put('/announcements/<int:announcement_id>')
@jwt_required()
@cross_origin()
def edit_announcement(announcement_id):
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'error': 'Announcement not found'}), HTTP_404_NOT_FOUND
    if announcement.author_id != admin.id:
        return jsonify({'error': 'Forbidden'}), HTTP_401_UNAUTHORIZED
    data = request.json or {}
    if 'title' in data: announcement.title = data['title'].strip()
    if 'content' in data: announcement.content = data['content'].strip()
    if 'image' in data: announcement.image = data['image']
    if 'is_pinned' in data: announcement.is_pinned = data['is_pinned']
    if 'is_visible' in data: announcement.is_visible = data['is_visible']
    db.session.commit()
    return jsonify({'message': 'Announcement updated', 'announcement': {'id': announcement.id, 'title': announcement.title, 'content': announcement.content, 'is_pinned': announcement.is_pinned, 'is_visible': announcement.is_visible, 'updated_at': announcement.updated_at.isoformat()}}), HTTP_200_OK


@auth.delete('/announcements/<int:announcement_id>')
@jwt_required()
@cross_origin()
def delete_announcement(announcement_id):
    user_id = get_jwt_identity()
    admin   = User.query.filter_by(identify=user_id).first()
    if not admin or admin.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'error': 'Announcement not found'}), HTTP_404_NOT_FOUND
    if announcement.author_id != admin.id:
        return jsonify({'error': 'Forbidden'}), HTTP_401_UNAUTHORIZED
    db.session.delete(announcement)
    db.session.commit()
    return jsonify({'message': 'Announcement deleted successfully'}), HTTP_200_OK


@auth.post('/projects')
@jwt_required()
@cross_origin()
def create_project():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data        = request.json or {}
    title       = data.get('title', '').strip()
    description = data.get('description')
    image       = data.get('image')
    category    = data.get('category', 'other')
    status      = data.get('status', 'open')
    is_visible  = data.get('is_visible', True)
    if not title:
        return jsonify({'error': 'title is required'}), HTTP_400_BAD_REQUEST
    project = Project(title=title, description=description, image=image, category=category, status=status, is_visible=is_visible, owner_id=user.id)
    db.session.add(project)
    db.session.commit()
    return jsonify({'message': 'Project created', 'project': {'id': project.id, 'title': project.title, 'category': project.category, 'status': project.status}}), HTTP_201_CREATED


@auth.get('/projects')
@jwt_required()
@cross_origin()
def get_projects():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    projects = Project.query.filter_by(is_visible=True).order_by(Project.created_at.desc()).all()
    return jsonify({'projects': [{'id': p.id, 'title': p.title, 'description': p.description, 'image': p.image, 'category': p.category, 'status': p.status, 'like_count': p.like_count, 'comment_count': p.comment_count, 'is_liked': p.likes.filter_by(user_id=user.id).first() is not None, 'owner': {'id': p.owner.id, 'firstname': p.owner.firstname, 'lastname': p.owner.lastname, 'image': p.owner.image, 'grade': p.owner.grade, 'domain': p.owner.domain}} for p in projects]}), HTTP_200_OK


@auth.post('/projects/<int:project_id>/like')
@jwt_required()
@cross_origin()
def toggle_project_like(project_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    project = Project.query.get(project_id)
    if not project or not project.is_visible:
        return jsonify({'error': 'Project not found'}), HTTP_404_NOT_FOUND
    existing = ProjectLike.query.filter_by(user_id=user.id, project_id=project.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': 'Like removed', 'liked': False, 'like_count': project.like_count}), HTTP_200_OK
    like = ProjectLike(user_id=user.id, project_id=project.id)
    db.session.add(like)
    db.session.commit()
    return jsonify({'message': 'Project liked', 'liked': True, 'like_count': project.like_count}), HTTP_201_CREATED


@auth.get('/projects/<int:project_id>/comments')
@jwt_required()
@cross_origin()
def get_project_comments(project_id):
    user_id = get_jwt_identity()
    if not User.query.filter_by(identify=user_id).first():
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    project = Project.query.get(project_id)
    if not project or not project.is_visible:
        return jsonify({'error': 'Project not found'}), HTTP_404_NOT_FOUND
    comments = project.comments.order_by(ProjectComment.created_at.asc()).all()
    return jsonify({'comments': [{'id': c.id, 'content': c.content, 'created_at': c.created_at.isoformat(), 'updated_at': c.updated_at.isoformat(), 'user': {'id': c.user.id, 'firstname': c.user.firstname, 'lastname': c.user.lastname, 'image': c.user.image}} for c in comments]}), HTTP_200_OK


@auth.post('/projects/<int:project_id>/comments')
@jwt_required()
@cross_origin()
def add_project_comment(project_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    project = Project.query.get(project_id)
    if not project or not project.is_visible:
        return jsonify({'error': 'Project not found'}), HTTP_404_NOT_FOUND
    data    = request.json or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'content is required'}), HTTP_400_BAD_REQUEST
    comment = ProjectComment(user_id=user.id, project_id=project.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added', 'comment': {'id': comment.id, 'content': comment.content, 'created_at': comment.created_at.isoformat(), 'user': {'id': user.id, 'firstname': user.firstname, 'lastname': user.lastname, 'image': user.image}}}), HTTP_201_CREATED


@auth.delete('/projects/<int:project_id>/comments/<int:comment_id>')
@jwt_required()
@cross_origin()
def delete_project_comment(project_id, comment_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    comment = ProjectComment.query.filter_by(id=comment_id, project_id=project_id).first()
    if not comment:
        return jsonify({'error': 'Comment not found'}), HTTP_404_NOT_FOUND
    if comment.user_id != user.id:
        return jsonify({'error': 'Forbidden'}), HTTP_401_UNAUTHORIZED
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted'}), HTTP_200_OK


@auth.post('/users/<int:target_id>/follow')
@jwt_required()
@cross_origin()
def toggle_follow(target_id):
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    ban_response = _check_banned(user)
    if ban_response:
        return ban_response
    if user.id == target_id:
        return jsonify({'error': 'You cannot follow yourself'}), HTTP_400_BAD_REQUEST
    target = User.query.get(target_id)
    if not target:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    existing = UserFollow.query.filter_by(follower_id=user.id, following_id=target.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': 'Unfollowed', 'following': False, 'followers_count': target.followers.count()}), HTTP_200_OK
    follow = UserFollow(follower_id=user.id, following_id=target.id)
    db.session.add(follow)
    db.session.commit()
    try:
        send_follow_email(follower_firstname=user.firstname, follower_lastname=user.lastname, follower_image=getattr(user, 'image', None), to_email=target.email, to_name=target.firstname)
    except Exception:
        pass
    return jsonify({'message': 'Following', 'following': True, 'followers_count': target.followers.count()}), HTTP_201_CREATED


@auth.get('/users/<int:target_id>/followers')
@jwt_required()
@cross_origin()
def get_followers(target_id):
    user_id = get_jwt_identity()
    if not User.query.filter_by(identify=user_id).first():
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    target = User.query.get(target_id)
    if not target:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    followers = [{'id': f.follower.id, 'firstname': f.follower.firstname, 'lastname': f.follower.lastname, 'image': f.follower.image, 'grade': f.follower.grade, 'domain': f.follower.domain} for f in target.followers.all()]
    return jsonify({'followers': followers, 'count': len(followers)}), HTTP_200_OK


@auth.get('/users/<int:target_id>/following')
@jwt_required()
@cross_origin()
def get_following(target_id):
    user_id = get_jwt_identity()
    if not User.query.filter_by(identify=user_id).first():
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    target = User.query.get(target_id)
    if not target:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    following = [{'id': f.following.id, 'firstname': f.following.firstname, 'lastname': f.following.lastname, 'image': f.following.image, 'grade': f.following.grade, 'domain': f.following.domain} for f in target.following.all()]
    return jsonify({'following': following, 'count': len(following)}), HTTP_200_OK


@auth.get('/stats')
@cross_origin()
def get_stats():
    return jsonify({'projects': Project.query.filter_by(is_visible=True).count(), 'events': Event.query.filter_by(is_visible=True).count()}), HTTP_200_OK


@auth.post('/search')
@jwt_required()
@cross_origin()
def search_students():
    user_id = get_jwt_identity()
    user    = User.query.filter_by(identify=user_id).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    ban_response = _check_banned(user)
    if ban_response:
        return ban_response
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), HTTP_400_BAD_REQUEST
    pattern = f"%{name}%"
    users = User.query.filter(db.or_(User.firstname.ilike(pattern), User.lastname.ilike(pattern), db.func.concat(User.firstname, ' ', User.lastname).ilike(pattern))).all()
    return jsonify({'results': [{'id': u.id, 'firstname': u.firstname, 'lastname': u.lastname, 'image': u.image} for u in users]}), HTTP_200_OK


@auth.post('/info')
@jwt_required()
@cross_origin()
def get_user_info():
    user_id = get_jwt_identity()
    me_user = User.query.filter_by(identify=user_id).first()
    if not me_user:
        return jsonify({'error': 'Unauthorized'}), HTTP_401_UNAUTHORIZED
    data      = request.json or {}
    target_id = data.get('id')
    if not target_id:
        return jsonify({'error': 'id is required'}), HTTP_400_BAD_REQUEST
    user = User.query.get(target_id)
    if not user:
        return jsonify({'error': 'User not found'}), HTTP_404_NOT_FOUND
    owned = [{'id': p.id, 'title': p.title, 'description': p.description, 'image': p.image, 'category': p.category, 'status': p.status, 'like_count': p.like_count, 'comment_count': p.comment_count} for p in user.owned_projects.filter_by(is_visible=True).all()]
    return jsonify({'user': {'id': user.id, 'firstname': user.firstname, 'lastname': user.lastname, 'email': user.email, 'phone': user.phone, 'image': user.image, 'grade': user.grade, 'domain': user.domain, 'created_at': user.created_at.isoformat() if user.created_at else None, 'followers_count': user.followers.count(), 'following_count': user.following.count(), 'is_following': UserFollow.query.filter_by(follower_id=me_user.id, following_id=user.id).first() is not None}, 'projects': owned}), HTTP_200_OK
