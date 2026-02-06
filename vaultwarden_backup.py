import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import os
import sys
import time
import json
os.environ['TZ'] = 'Asia/Shanghai'  # 强制设置为北京时间
time.tzset()  # 让时区生效
# --- 配置读取（从环境变量获取） ---
# Bitwarden 配置
BW_SERVER = os.getenv("BW_SERVER", "https://vault.bitwarden.com")
BW_EMAIL = os.getenv("BW_EMAIL")
BW_PASSWORD = os.getenv("BW_PASSWORD")

# 邮件配置
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # 邮箱授权码
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.qq.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 465))
EMAIL_RECEIVERS = os.getenv("EMAIL_RECEIVERS", EMAIL_USER)  # 多个收件人用逗号分隔

# 脚本基础配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BW_CMD_PATH = os.path.join(SCRIPT_DIR, "bw")  # bw 命令路径
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")

# 确保导出目录存在
os.makedirs(EXPORT_DIR, exist_ok=True)

def run_command(cmd, timeout=120):
    """
    执行系统命令并返回结果
    :param cmd: 命令字符串
    :param timeout: 超时时间
    :return: (stdout, stderr, returncode)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", f"命令执行超时（{timeout}秒）", -1
    except Exception as e:
        return "", f"命令执行异常: {str(e)}", -2

def send_email_with_attachment(
    smtp_server, smtp_port, sender, password,
    receivers, subject, content, attachment_path=None
):
    """
    发送带附件的邮件
    """
    # 处理收件人列表
    if isinstance(receivers, str):
        receivers = [r.strip() for r in receivers.split(',')]

    # 1. 构建邮件对象
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ", ".join(receivers)
    msg['Subject'] = subject

    # 2. 添加邮件正文
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    # 3. 添加附件
    if attachment_path and os.path.exists(attachment_path):
        filename = os.path.basename(attachment_path)
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
        print(f"✅ 附件 {filename} 加载成功")
    elif attachment_path:
        print(f"❌ 附件路径不存在：{attachment_path}")
        return False

    # 4. 发送邮件
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, receivers, msg.as_string())
        print(f"✅ 邮件发送成功！收件人：{receivers}")
        return True
    except smtplib.SMTPException as e:
        print(f"❌ 邮件发送失败：{str(e)}")
        return False
    except Exception as e:
        print(f"❌ 未知错误：{str(e)}")
        return False

def export_bitwarden_and_send_email():
    """
    核心业务逻辑：导出 Bitwarden 密码并发送邮件
    """
    # 前置检查：环境变量是否完整
    if not all([BW_EMAIL, BW_PASSWORD, EMAIL_USER, EMAIL_PASSWORD]):
        print("❌ 错误：请设置必要的环境变量 (BW_EMAIL, BW_PASSWORD, EMAIL_USER, EMAIL_PASSWORD)")
        return False

    strTime = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    OUTPUT_FILE = os.path.join(EXPORT_DIR, f"{strTime}.json")

    try:
        # 1. 检查 bw 命令
        if not os.path.exists(BW_CMD_PATH):
            print(f"❌ 未找到 bw 命令，路径：{BW_CMD_PATH}")
            return False
        bw_cmd = BW_CMD_PATH

        # 2. 清理旧会话
        print("🔄 清理旧会话...")
        cmd = f"{bw_cmd} logout"
        stdout, stderr, rc = run_command(cmd)
        if rc != 0 and "not logged in" not in stderr.lower():
            print(f"❌ 退出登录失败：{stderr}")

        # 3. 配置服务器
        print(f"🔄 配置 Bitwarden 服务器：{BW_SERVER}")
        cmd = f"{bw_cmd} config server {BW_SERVER}"
        stdout, stderr, rc = run_command(cmd)
        if rc != 0:
            print(f"❌ 服务器配置失败：{stderr}")
            return False

        # 4. 登录
        print("🔄 登录 Bitwarden...")
        cmd = f"echo '{BW_PASSWORD}' | {bw_cmd} login {BW_EMAIL}"
        stdout, stderr, rc = run_command(cmd, timeout=60)
        if rc != 0:
            error_msg = f"登录失败：{stderr}"
            if "master password is incorrect" in stderr.lower():
                error_msg += "（主密码错误）"
            elif "network" in stderr.lower():
                error_msg += "（网络/服务器地址错误）"
            print(f"❌ {error_msg}")
            return False

        # 5. 导出密码
        print("🔄 导出密码库...")
        cmd = f"echo '{BW_PASSWORD}' | {bw_cmd} export --format json --output {OUTPUT_FILE}"
        stdout, stderr, rc = run_command(cmd, timeout=60)
        if rc != 0:
            print(f"❌ 导出失败：{stderr}")
            return False

        if not os.path.exists(OUTPUT_FILE):
            print(f"⚠️ 命令执行成功，但未找到导出文件：{OUTPUT_FILE}")
            return False

        # 6. 发送邮件
        print("🔄 发送备份邮件...")
        title = f"Bitwarden 密码备份 {strTime}"
        content = f"Bitwarden 密码备份完成\n备份时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n文件大小：{os.path.getsize(OUTPUT_FILE) / 1024:.2f} KB"
        
        email_result = send_email_with_attachment(
            smtp_server=EMAIL_SMTP_HOST,
            smtp_port=EMAIL_SMTP_PORT,
            sender=EMAIL_USER,
            password=EMAIL_PASSWORD,
            receivers=EMAIL_RECEIVERS,
            subject=title,
            content=content,
            attachment_path=OUTPUT_FILE
        )

        if email_result:
            print("✅ 备份流程全部完成！")
            return True
        else:
            print("❌ 密码导出成功，但邮件发送失败")
            return False

    except Exception as e:
        print(f"❌ 执行异常：{str(e)}")
        return False
    finally:
        # 确保退出登录
        run_command(f"{bw_cmd} logout")
        print("🔄 已退出 Bitwarden 登录")

if __name__ == "__main__":
    print("=== Bitwarden 自动备份脚本启动 ===")
    success = export_bitwarden_and_send_email()
    sys.exit(0 if success else 1)