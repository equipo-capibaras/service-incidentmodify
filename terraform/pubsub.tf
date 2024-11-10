resource "google_pubsub_topic" "incident_update" {
  name = "incident-update"
}

data "google_iam_policy" "pubusb" {
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
  policy_data = data.google_iam_policy.pubusb.policy_data
}
