"""Subscription plan enumeration."""

from enum import Enum


class SubscriptionPlan(str, Enum):
    """Available subscription plans for tenants."""

    STARTER = "starter"  # Entry-level plan with basic features
    PROFESSIONAL = "professional"  # Professional features with higher limits
    ENTERPRISE = "enterprise"  # Enterprise plan with custom features
