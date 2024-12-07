resource "google_iap_client" "oauth_clients" {
  for_each = var.oauth_clients

  brand {
    support_email     = each.value.support_email
    application_title = each.value.application_title
  }

  oauth2_client {
    client_name = each.value.client_name
    secret      = random_password.oauth_secret.result
  }
}

resource "random_password" "oauth_secret" {
  length  = 16
  special = true
}
