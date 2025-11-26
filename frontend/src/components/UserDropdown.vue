<template>
  <div class="dropdown">
    <button class="btn btn-outline-secondary btn-sm dropdown-toggle" data-bs-toggle="dropdown">
      {{ username }}
    </button>
    <ul class="dropdown-menu dropdown-menu-end">
      <li><router-link class="dropdown-item" to="/cabinet">Personal Cabinet</router-link></li>
      <li><a class="dropdown-item" href="#">Log out</a></li>
    </ul>
  </div>
</template>

<script setup>
const username = 'Ranjithsiji' // replace with auth integration later
</script>
