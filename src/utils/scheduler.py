"""
定时提醒调度器
基于 APScheduler 实现
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..config.settings import settings
from ..utils.logging import get_logger
from ..db.models import db_manager
from ..db.repository import ReminderRepository

logger = get_logger(__name__)


class ReminderScheduler:
    """
    提醒调度器
    
    功能：
    - 定时检查待发送提醒
    - 支持一次性/重复提醒
    - 多种通知渠道
    """
    
    _instance = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _notification_handlers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_scheduler(self):
        """初始化调度器"""
        if self._scheduler is not None:
            return
        
        try:
            self._scheduler = AsyncIOScheduler(
                timezone=settings.timezone if hasattr(settings, 'timezone') else "Asia/Shanghai"
            )
            
            # 添加每分钟检查一次待发送提醒的任务
            self._scheduler.add_job(
                self._check_pending_reminders,
                trigger=IntervalTrigger(minutes=1),
                id="check_reminders",
                replace_existing=True
            )
            
            self._scheduler.start()
            logger.info("✅ 提醒调度器已启动")
            
        except Exception as e:
            logger.error(f"提醒调度器启动失败: {e}")
            self._scheduler = None
    
    def shutdown(self):
        """关闭调度器"""
        if self._scheduler:
            self._scheduler.shutdown()
            logger.info("提醒调度器已关闭")
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """
        注册通知处理器
        
        Args:
            channel: 通知渠道名称 (in_app, email, feishu)
            handler: 处理函数 async def handler(reminder)
        """
        self._notification_handlers[channel] = handler
        logger.info(f"已注册通知处理器: {channel}")
    
    async def _check_pending_reminders(self):
        """检查待发送的提醒"""
        try:
            session = db_manager.get_session()
            try:
                repo = ReminderRepository(session)
                now = datetime.now()
                
                # 获取待发送的提醒
                pending = repo.get_pending_reminders(now)
                
                if pending:
                    logger.info(f"发现 {len(pending)} 个待发送提醒")
                    
                    for reminder in pending:
                        await self._send_reminder(reminder, repo)
                        
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"检查提醒失败: {e}")
    
    async def _send_reminder(self, reminder, repo: ReminderRepository):
        """
        发送提醒
        
        Args:
            reminder: 提醒对象
            repo: 数据仓库
        """
        logger.info(f"发送提醒: {reminder.title} (用户: {reminder.user_id[:8]}...)")
        
        # 标记为已发送
        repo.mark_as_sent(reminder.id)
        
        # 发送通知到各个渠道
        channels = reminder.notify_channels or ["in_app"]
        
        for channel in channels:
            handler = self._notification_handlers.get(channel)
            if handler:
                try:
                    await handler(reminder)
                except Exception as e:
                    logger.error(f"{channel} 通知失败: {e}")
            else:
                # 默认处理：记录日志
                logger.info(f"[{channel}] {reminder.title}: {reminder.description}")
        
        # 如果是重复提醒，创建下一个
        if reminder.is_recurring:
            await self._create_next_recurrence(reminder, repo)
    
    async def _create_next_recurrence(self, reminder, repo: ReminderRepository):
        """
        创建下一个重复提醒
        
        Args:
            reminder: 当前提醒
            repo: 数据仓库
        """
        rule = reminder.recurrence_rule or {}
        recurrence_type = rule.get("type", "daily")
        interval = rule.get("interval", 1)
        
        # 计算下一次时间
        if recurrence_type == "daily":
            next_time = reminder.remind_at + timedelta(days=interval)
        elif recurrence_type == "weekly":
            next_time = reminder.remind_at + timedelta(weeks=interval)
        elif recurrence_type == "monthly":
            # 简单处理：每月同一天
            from dateutil.relativedelta import relativedelta
            next_time = reminder.remind_at + relativedelta(months=interval)
        else:
            next_time = reminder.remind_at + timedelta(days=interval)
        
        # 创建新提醒
        try:
            new_reminder = repo.create(
                user_id=reminder.user_id,
                title=reminder.title,
                description=reminder.description,
                remind_at=next_time,
                timezone=reminder.timezone,
                is_recurring=True,
                recurrence_rule=rule,
                notify_channels=reminder.notify_channels,
                task_id=reminder.task_id
            )
            logger.info(f"已创建下一次重复提醒: {new_reminder.id}")
        except Exception as e:
            logger.error(f"创建重复提醒失败: {e}")
    
    def schedule_one_time_reminder(self, reminder_id: str, remind_at: datetime):
        """
        调度一次性提醒（APScheduler 任务）
        
        Args:
            reminder_id: 提醒 ID
            remind_at: 提醒时间
        """
        if not self._scheduler:
            return
        
        job_id = f"reminder_{reminder_id}"
        
        # 移除已存在的任务
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        
        # 添加新任务
        self._scheduler.add_job(
            self._trigger_reminder,
            trigger=DateTrigger(run_date=remind_at),
            id=job_id,
            args=[reminder_id],
            replace_existing=True
        )
        
        logger.debug(f"已调度提醒: {reminder_id} at {remind_at}")
    
    async def _trigger_reminder(self, reminder_id: str):
        """触发指定提醒"""
        session = db_manager.get_session()
        try:
            from ..db.models import Reminder
            reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder and reminder.status == "pending":
                repo = ReminderRepository(session)
                await self._send_reminder(reminder, repo)
        finally:
            session.close()


# 全局调度器实例
reminder_scheduler = ReminderScheduler()


# ============================================================================
# 通知处理器示例
# ============================================================================

async def in_app_notification(reminder):
    """应用内通知（存储到数据库供前端轮询）"""
    logger.info(f"[应用内通知] {reminder.title}")
    # 这里可以将通知存储到专门的 notifications 表
    # 前端通过 API 轮询获取


async def feishu_notification(reminder):
    """飞书通知（预留）"""
    logger.info(f"[飞书通知] {reminder.title}")
    # 需要配置飞书 webhook
    # 待实现


async def email_notification(reminder):
    """邮件通知（预留）"""
    logger.info(f"[邮件通知] {reminder.title}")
    # 需要配置 SMTP
    # 待实现


def init_scheduler():
    """初始化提醒调度器"""
    # 注册默认通知处理器
    reminder_scheduler.register_notification_handler("in_app", in_app_notification)
    reminder_scheduler.register_notification_handler("feishu", feishu_notification)
    reminder_scheduler.register_notification_handler("email", email_notification)
    
    # 启动调度器
    reminder_scheduler.init_scheduler()
