import { Component, OnInit } from '@angular/core';
import { AppContextService, IAppContext } from "../../services/app-context.service";
import { LegacyRoutesService } from "../../services/legacy-routes.service";
import { UsersService } from "../../services/users.service";

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  appContext: IAppContext;

  constructor(appContext: AppContextService, public legacyRoutes: LegacyRoutesService,
              public usersService: UsersService) {
    this.appContext = appContext.get();
  }

  ngOnInit() {
  }
}
