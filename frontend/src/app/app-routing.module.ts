import { NgModule } from "@angular/core";
import { RouterModule, Routes } from "@angular/router";

const routes: Routes = [
  {
    path: "account",
    loadChildren: () => import("@features/account/account.module").then(m => m.AccountModule)
  },
  {
    path: "dev",
    loadChildren: () => import("@features/dev/dev.module").then(m => m.DevModule)
  },
  {
    path: "i",
    loadChildren: () => import("@features/image/image.module").then(m => m.ImageModule)
  },
  {
    path: "iotd",
    loadChildren: () => import("@features/iotd/iotd.module").then(m => m.IotdModule)
  },
  {
    path: "notifications",
    loadChildren: () => import("@features/notifications/notifications.module").then(m => m.NotificationsModule)
  },
  {
    path: "permission-denied",
    loadChildren: () =>
      import("@features/permission-denied/permission-denied.module").then(m => m.PermissionDeniedModule)
  },
  {
    path: "subscriptions",
    loadChildren: () => import("@features/subscriptions/subscriptions.module").then(m => m.SubscriptionsModule)
  },
  {
    path: "uploader",
    loadChildren: () => import("@features/uploader/uploader.module").then(m => m.UploaderModule)
  },
  {
    path: "**",
    loadChildren: () => import("@features/not-found-404/not-found-404.module").then(m => m.NotFound404Module)
  }
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      onSameUrlNavigation: "reload",
      relativeLinkResolution: "legacy"
    })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
