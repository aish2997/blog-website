resource "google_dns_managed_zone" "my_zone" {
  count      = var.environment == "prod" ? 1 : 0
  name       = "europe-west1"
  dns_name   = "aishwaryabhargava.com." # Replace with your domain
  visibility = "public"
}

# CNAME Record for www subdomain
resource "google_dns_record_set" "www_cname_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "www.aishwaryabhargava.com."
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "CNAME"
  ttl          = 300

  rrdatas = ["c.storage.googleapis.com."]
}

# CNAME Record for root domain (redirect to www)
resource "google_dns_record_set" "root_cname_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "aishwaryabhargava.com."
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "CNAME"
  ttl          = 300

  rrdatas = ["www.aishwaryabhargava.com."]
}

resource "google_dns_record_set" "txt_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "TXT"
  ttl          = 300 # 5 minutes

  rrdatas = ["\"google-site-verification=_uxv0Dluo1-dq7JfKyCPwzkr-ClXtPymYWDnrTXezPk\""]
}