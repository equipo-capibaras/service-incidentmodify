resource "google_pubsub_topic" "incident_update" {
  name = "incident-update"
}

resource "google_pubsub_topic" "incident_alert" {
  name = "incident-alert"
}

resource "google_pubsub_topic" "incident_risk_updated" {
  name = "incident-risk-updated"
}


data "google_iam_policy" "pubsub" {
  binding {
    role = "roles/pubsub.publisher"
    members = [
      google_service_account.service.member,
    ]
  }
}

resource "google_pubsub_topic_iam_policy" "incident_update" {
  project = google_pubsub_topic.incident_update.project
  topic = google_pubsub_topic.incident_update.name
  policy_data = data.google_iam_policy.pubsub.policy_data
}

resource "google_pubsub_topic_iam_policy" "incident_alert" {
  project = google_pubsub_topic.incident_alert.project
  topic = google_pubsub_topic.incident_alert.name
  policy_data = data.google_iam_policy.pubsub.policy_data
}

resource "google_pubsub_topic_iam_policy" "incident_risk_updated" {
  project = google_pubsub_topic.incident_risk_updated.project
  topic = google_pubsub_topic.incident_risk_updated.name
  policy_data = data.google_iam_policy.pubsub.policy_data
}
