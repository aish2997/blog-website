resource "google_iap_brand" "oauth_clients" {
  for_each = var.oauth_clients

  support_email     = each.value.support_email
  application_title = each.value.application_title
}

resource "random_password" "oauth_secret" {
  for_each = var.oauth_clients

  length  = 16
  special = true
}

resource "google_iap_client" "oauth_clients" {
  for_each = var.oauth_clients

  brand        = google_iap_brand.oauth_clients[each.key].name
  display_name = each.value.client_name
  secret       = random_password.oauth_secret[each.key].result
}

output "oauth_client_secrets" {
  value = {
    for k, client in google_iap_client.oauth_clients : k => {
      client_id     = client.client_id
      client_secret = client.secret
    }
  }
}
