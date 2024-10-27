# Enables the Firestore API for the project.
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Grants the service account the "Datastore User" role on the project.
# This allows the service account (this microservice) to access the firestore database.
resource "google_project_iam_member" "firestore" {
  project = local.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.service.member
}

# Grants the service account the "Datastore Import/Export Admin" role on the project.
# This allows the service account to backup the firestore database.
resource "google_project_iam_member" "firestore_backup" {
  project = local.project_id
  role    = "roles/datastore.importExportAdmin"
  member  = google_service_account.service.member
}

# Creates a Firestore database for this microservice.
resource "google_firestore_database" "default" {
  name                              = local.database_name
  location_id                       = local.region
  type                              = "FIRESTORE_NATIVE"
  deletion_policy                   = "DELETE"
  delete_protection_state           = "DELETE_PROTECTION_DISABLED"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"

  depends_on = [ google_project_service.firestore ]
}

resource "google_firestore_index" "query-by-reporter-idx" {
  database   = google_firestore_database.default.name
  collection = "incidents"

  fields {
    field_path = "reported_by"
    order      = "ASCENDING"
  }

  fields {
    field_path = "last_modified"
    order      = "DESCENDING"
  }
}
