<template>
  <div class="card p-3">
    <h6 class="mb-2">Article metadata</h6>
    <table class="table table-sm">
      <tbody>
        <tr><th>Title</th><td>{{ meta.title || '—' }}</td></tr>
        <tr><th>Added On</th><td>{{ meta.addedOn || '—' }}</td></tr>
        <tr><th>Last Edit</th><td>{{ meta.lastEdit || '—' }}</td></tr>
        <tr><th>Bytes</th><td>{{ meta.bytes || 0 }}</td></tr>
        <tr><th>Words</th><td>{{ meta.wordCount || 0 }}</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ meta: Object })
</script>
