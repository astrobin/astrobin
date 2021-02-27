export interface ImageInterface {
  user: number;
  pk: number;
  hash: string;
  title: string;
  imageFile: string;
  isWip: boolean;
  skipNotifications: boolean;
  w: number;
  h: number;
  imagingTelescopes: number[];
  imagingCameras: number[];
  published: string;
}
