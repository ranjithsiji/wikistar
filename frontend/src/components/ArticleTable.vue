<template>
  <div>
    <table class="table table-hover">
      <thead class="table-light">
        <tr>
          <th>Article</th>
          <th>Added</th>
          <th>Last edit</th>
          <th>Bytes</th>
          <th>Marks</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in articles" :key="a.id" @click="$emit('select', a)" style="cursor:pointer">
          <td>{{ a.title }}</td>
          <td>{{ a.addedOn ? new Date(a.addedOn).toLocaleString() : '—' }}</td>
          <td>{{ a.lastEdit ? new Date(a.lastEdit).toLocaleString() : '—' }}</td>
          <td>{{ a.bytes || 0 }}</td>
          <td>{{ Object.keys(a.marksBy||{}).length }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ articles: Array })
</script>
