from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_master_whatsapp,
    admin,
    ai_assistant,
    admin_prompt_construtor,
    agencies,
    agency_domains,
    agency_team,
    auth,
    billing,
    clients,
    checkout,
    documents,
    flight_api_keys,
    flight_sections,
    lead_forms,
    lead_crm,
    lessons,
    media,
    pages,
    pixels,
    webhook_notifications,
    public_lead_forms,
    public_pages,
    stats,
    system_banners,
    templates,
    whatsapp,
    whatsapp_ws,
    whatsapp_webhooks,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agencies.router, prefix="/agencies", tags=["agencies"])
api_router.include_router(
    agency_domains.router,
    prefix="/agencies/me/domains",
    tags=["agency-domains"],
)
api_router.include_router(agency_team.router, tags=["agency-team"])
api_router.include_router(templates.router, prefix="/page-templates", tags=["page-templates"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(public_pages.router, prefix="/public/pages", tags=["public-pages"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
api_router.include_router(pixels.router, prefix="/pixels", tags=["pixels"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ai_assistant.router, prefix="/ai-assistant", tags=["ai-assistant"])
api_router.include_router(admin_master_whatsapp.router, prefix="/admin-master/whatsapp", tags=["admin-master-whatsapp"])
api_router.include_router(admin_prompt_construtor.router, prefix="/admin-master", tags=["admin-master-prompt-construtor"])
api_router.include_router(webhook_notifications.admin_router, tags=["admin-master-webhook-notifications"])
api_router.include_router(webhook_notifications.router, tags=["webhook-notifications"])
api_router.include_router(flight_api_keys.router, prefix="/admin", tags=["flight-api-keys"])
api_router.include_router(flight_sections.router, tags=["flight-sections"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(lead_forms.router, prefix="/lead-forms", tags=["lead-forms"])
api_router.include_router(lead_crm.router, prefix="/lead-forms", tags=["lead-crm"])
api_router.include_router(public_lead_forms.router, prefix="/public/lead-forms", tags=["public-lead-forms"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(system_banners.router, prefix="/system-banners", tags=["system-banners"])
api_router.include_router(system_banners.admin_router, tags=["admin-system-banners"])
api_router.include_router(checkout.admin_router, tags=["admin-checkout"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(
    whatsapp_webhooks.router,
    prefix="/webhooks/whatsapp",
    tags=["whatsapp-webhooks"],
)
api_router.include_router(whatsapp_ws.router, prefix="/whatsapp", tags=["whatsapp-ws"])
