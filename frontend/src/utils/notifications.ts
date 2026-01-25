import { notifications } from '@mantine/notifications';

export const showSuccess = (message: string, title?: string) => {
  notifications.show({
    title: title || 'Success',
    message,
    color: 'primary',
    autoClose: 5000,
  });
};

export const showError = (message: string, title?: string) => {
  notifications.show({
    title: title || 'Error',
    message,
    color: 'error',
    autoClose: 7000,
  });
};

export const showInfo = (message: string, title?: string) => {
  notifications.show({
    title: title || 'Info',
    message,
    color: 'accent',
    autoClose: 5000,
  });
};

export const showWarning = (message: string, title?: string) => {
  notifications.show({
    title: title || 'Warning',
    message,
    color: 'warning',
    autoClose: 6000,
  });
};
