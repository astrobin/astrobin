import { Routes } from "@angular/router";
import { NotificationsPageComponent } from "@features/notifications/pages/notifications-page/notifications-page.component";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";

export const routes: Routes = [
  {
    path: "",
    component: NotificationsPageComponent,
    canActivate: [AuthGuardService]
  }
];
