resource "google_dns_managed_zone" "my_zone" {
  name       = "europe-west1"
  dns_name   = "aishwaryabhargava.com." # Replace with your domain
  visibility = "public"
}

resource "google_dns_record_set" "cname_record" {
  name         = "www.aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone.name
  type         = "CNAME"
  ttl          = 300

  rrdatas = ["c.storage.googleapis.com."] # GCS bucket URL for static website hosting
}

resource "google_dns_record_set" "a_record" {
  name         = "aishwaryabhargava.com." # Replace with your actual domain
  managed_zone = google_dns_managed_zone.my_zone.name
  type         = "A"
  ttl          = 300

  rrdatas = ["216.239.32.21", "216.239.34.21", "216.239.36.21", "216.239.38.21"] # These are GCS IP addresses for static website hosting
}
