#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <string.h>

#define SHM_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./shared_mem_bin <write/read/delete> [message]\n");
        return 1;
    }

    key_t key = ftok("shmfile", 65);
    int shmid = shmget(key, SHM_SIZE, 0666 | IPC_CREAT);
    char *data;

    if (strcmp(argv[1], "write") == 0 && argc == 3) {
        data = (char *)shmat(shmid, NULL, 0);
        strncpy(data, argv[2], SHM_SIZE);
        shmdt(data);
        printf("✅ Message written: %s\n", argv[2]);
    } else if (strcmp(argv[1], "read") == 0) {
        data = (char *)shmat(shmid, NULL, 0);
        printf("📖 Message read: %s\n", data);
        shmdt(data);
    } else if (strcmp(argv[1], "delete") == 0) {
        shmctl(shmid, IPC_RMID, NULL);
        printf("🗑️ Shared memory segment removed.\n");
    } else {
        printf("❌ Invalid command or missing message.\n");
    }

    return 0;
}
