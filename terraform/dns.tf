resource "google_dns_managed_zone" "my_zone" {
  count      = var.environment == "prod" ? 1 : 0
  name       = "europe-west1"
  dns_name   = "aishwaryabhargava.com." # Replace with your domain
  visibility = "public"
}

resource "google_dns_record_set" "cname_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "www.aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "CNAME"
  ttl          = 300

  rrdatas = ["c.storage.googleapis.com."] # GCS bucket URL for static website hosting
}

resource "google_dns_record_set" "a_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "A"
  ttl          = 300

  rrdatas = ["216.239.32.21", "216.239.34.21", "216.239.36.21", "216.239.38.21"] # These are GCS IP addresses for static website hosting
}

resource "google_dns_record_set" "txt_record" {
  count        = var.environment == "prod" ? 1 : 0
  name         = "aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone[0].name
  type         = "TXT"
  ttl          = 300 # 5 minutes

  rrdatas = ["\"google-site-verification=_uxv0Dluo1-dq7JfKyCPwzkr-ClXtPymYWDnrTXezPk\""]
}