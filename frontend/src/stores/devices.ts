import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import type {DeviceRead} from '@/api'
import {Devices} from '@/api'


export const useDeviceStore = defineStore('devices', () => {
  // State
  const loading = ref(false);
  const error = ref<string | null>(null);
  const devices = ref<DeviceRead[]>([]);

  // Getters
  const all = computed(() => devices.value);
  const byID = (id: number) => computed(() => devices.value.find(d => d.id === id));
  // Actions

    async function load() {
        loading.value = true;
        error.value = null;
        try {
            const { data } = await Devices.devicesList();
            devices.value = data;
        } catch (err) {
            console.error('Failed to load devices:', err);
            error.value = 'Failed to load devices.';
        } finally {
            loading.value = false;
        }
    }

  return {
    // State
    devices,
    loading,
    error,

    // Getters
    all,
      byID,

    // Actions
    load,
  };
});
