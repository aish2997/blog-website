resource "google_bigquery_dataset" "datasets" {
  for_each = var.bigquery_datasets

  dataset_id = "${each.key}_${var.environment}" # Combines dataset name with environment
  location   = each.value.location

  labels = {
    environment = var.environment
  }
}


resource "google_bigquery_table" "tables" {
  for_each = var.bigquery_tables

  dataset_id = google_bigquery_dataset.datasets[each.key].dataset_id
  table_id   = each.key
  schema     = file(each.value.schema_file)
  time_partitioning {
    type = each.value.partition
  }
}
