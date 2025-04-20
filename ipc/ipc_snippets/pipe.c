#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>

int main() {
    int fd[2];
    char buf[100];
    if (pipe(fd) == -1) {
        perror("pipe failed");
        return 1;
    }

    pid_t pid = fork();
    if (pid == 0) {
        // Child
        close(fd[0]); // close read end
        char *msg = "Hello from child via pipe";
        write(fd[1], msg, strlen(msg));
        close(fd[1]);
    } else {
        // Parent
        wait(NULL);
        close(fd[1]); // close write end
        read(fd[0], buf, sizeof(buf));
        printf("Parent received: %s\n", buf);
        close(fd[0]);
    }

    return 0;
}
