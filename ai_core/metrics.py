from prometheus_client import Counter, Summary, disable_created_metrics

disable_created_metrics()

onboardings_total = Counter("onboardings_total", "Total started onboardings")
onboardings_completed_total = Counter("onboardings_completed_total", "Total completed onboarding")
onboardings_time = Summary("onboardings_time", "Time spent for onboarding")
