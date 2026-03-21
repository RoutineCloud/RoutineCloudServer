import {defineStore} from 'pinia'
import {ref} from 'vue'
import {FriendRead, Friends} from '@/api'

export const useFriendsStore = defineStore('friends', () => {
  const friends = ref<FriendRead[]>([])
  const friendRequests = ref<FriendRead[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFriends() {
    loading.value = true
    error.value = null
    try {
      const response = await Friends.friendsList()
      friends.value = response.data || []
      
      const requestsResponse = await Friends.friendsRequestsList()
      friendRequests.value = requestsResponse.data || []
    } catch (e: any) {
      console.error('Failed to fetch friends:', e)
      error.value = e.body?.detail || 'Failed to fetch friends'
    } finally {
      loading.value = false
    }
  }

  async function addFriend(friendCode: string) {
    loading.value = true
    error.value = null
    try {
      const response = await Friends.friendsAdd({ body: { friend_code: friendCode } })
      await fetchFriends()
      return (response.data as any)?.message || 'Friend request sent!'
    } catch (e: any) {
      error.value = e.body?.detail || 'Failed to add friend'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function acceptRequest(friendId: number) {
    try {
      await Friends.friendsAccept({path: { friend_id: friendId }})
      await fetchFriends()
    } catch (e: any) {
      error.value = e.body?.detail || 'Failed to accept friend request'
      throw e
    }
  }

  async function declineRequest(friendId: number) {
    try {
      await Friends.friendsDecline({ path: { friend_id: friendId } })
      await fetchFriends()
    } catch (e: any) {
      error.value = e.body?.detail || 'Failed to decline friend request'
      throw e
    }
  }

  async function removeFriend(friendId: number) {
    try {
      await Friends.friendsRemove({ path: { friend_id: friendId } })
      await fetchFriends()
    } catch (e: any) {
      error.value = e.body?.detail || 'Failed to remove friend'
      throw e
    }
  }

  return {
    friends,
    friendRequests,
    loading,
    error,
    fetchFriends,
    addFriend,
    acceptRequest,
    declineRequest,
    removeFriend
  }
})
