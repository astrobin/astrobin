import { Routes } from "@angular/router";
import { ImageEditPageComponent } from "@features/image/pages/edit/image-edit-page.component";
import { ImageResolver } from "@shared/resolvers/image.resolver";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";

export const routes: Routes = [
  {
    path: ":imageId/edit",
    component: ImageEditPageComponent,
    canActivate: [AuthGuardService],
    resolve: {
      image: ImageResolver
    }
  }
];
