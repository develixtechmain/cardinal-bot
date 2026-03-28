from prometheus_client import Counter, Summary, disable_created_metrics

disable_created_metrics()

users_total = Counter("users_total", "Total number of registered users")
users_tokens_total = Counter("users_tokens_total", "Users that requested token", ["user_id", "service", "username"])
users_linked_total = Counter("users_linked_total", "Users who linked channel")

users_trials_total = Counter("users_trials_total", "Count of user trials", ["user_id"])
payments_completed_total = Counter("payments_completed_total", "Count of completed user payments", ["user_id"])
revenue_total = Counter("revenue_total", "Total revenue")

leads_time = Summary("leads_time", "Time spent for message to become lead")
leads_actions_total = Counter("lead_action_total", "Lead accept/decline count", ["action"])
