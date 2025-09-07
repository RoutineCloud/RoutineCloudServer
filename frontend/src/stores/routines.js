import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useRoutinesStore = defineStore('routines', () => {
  // State
  const routines = ref([]);
  const loading = ref(false);
  const error = ref(null);

  // Getters
  const allRoutines = computed(() => routines.value);
  const activeRoutines = computed(() => 
    routines.value.filter(routine => routine.isActive)
  );
  const getRoutineById = (id) => 
    computed(() => routines.value.find(routine => routine.id === id));

  // Actions
  async function fetchRoutines() {
    loading.value = true;
    error.value = null;
    
    try {
      // In a real app, you would make an API call here
      // const response = await api.getRoutines();
      
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Set mock data
      routines.value = [
        { id: 1, name: 'Morning Routine', time: '07:00:00', isActive: true },
        { id: 2, name: 'Evening Routine', time: '22:00:00', isActive: true },
        { id: 3, name: 'Weekend Routine', time: '09:00:00', isActive: false }
      ];
    } catch (err) {
      console.error('Failed to fetch routines:', err);
      error.value = 'Failed to load routines. Please try again.';
    } finally {
      loading.value = false;
    }
  }

  async function addRoutine(routine) {
    loading.value = true;
    error.value = null;
    
    try {
      // In a real app, you would make an API call here
      // const response = await api.createRoutine(routine);
      
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Generate a new ID (in a real app, this would come from the backend)
      const newId = Math.max(0, ...routines.value.map(r => r.id)) + 1;
      
      // Add the new routine to the state
      const newRoutine = {
        id: newId,
        ...routine
      };
      
      routines.value.push(newRoutine);
      return newRoutine;
    } catch (err) {
      console.error('Failed to add routine:', err);
      error.value = 'Failed to create routine. Please try again.';
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function updateRoutine(id, updates) {
    loading.value = true;
    error.value = null;
    
    try {
      // In a real app, you would make an API call here
      // const response = await api.updateRoutine(id, updates);
      
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Find the routine in the state
      const index = routines.value.findIndex(r => r.id === id);
      
      if (index !== -1) {
        // Update the routine
        const updatedRoutine = {
          ...routines.value[index],
          ...updates
        };
        
        routines.value[index] = updatedRoutine;
        return updatedRoutine;
      }
      
      throw new Error('Routine not found');
    } catch (err) {
      console.error('Failed to update routine:', err);
      error.value = 'Failed to update routine. Please try again.';
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function deleteRoutine(id) {
    loading.value = true;
    error.value = null;
    
    try {
      // In a real app, you would make an API call here
      // const response = await api.deleteRoutine(id);
      
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Remove the routine from the state
      routines.value = routines.value.filter(r => r.id !== id);
      return true;
    } catch (err) {
      console.error('Failed to delete routine:', err);
      error.value = 'Failed to delete routine. Please try again.';
      return false;
    } finally {
      loading.value = false;
    }
  }

  return {
    // State
    routines,
    loading,
    error,
    
    // Getters
    allRoutines,
    activeRoutines,
    getRoutineById,
    
    // Actions
    fetchRoutines,
    addRoutine,
    updateRoutine,
    deleteRoutine
  };
});