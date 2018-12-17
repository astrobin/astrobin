import { Component, OnInit } from '@angular/core';
import { AppContextService, IAppContext } from "../../services/app-context.service";
import { LegacyRoutesService } from "../../services/legacy-routes.service";
import { UsersService } from "../../services/users.service";

interface IFlag {
  languageCode: string;
  countryCode: string;
  label: string;
}

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  appContext: IAppContext;
  flags: IFlag[] = [
    {languageCode: "en", countryCode: "us", label: "English (US)"},
    {languageCode: "en-GB", countryCode: "gb", label: "English (UK)"},
    {languageCode: "it", countryCode: "it", label: "Italiano"},
    {languageCode: "es", countryCode: "es", label: "Español"},
    {languageCode: "fr", countryCode: "fr", label: "Français"},
    {languageCode: "fi", countryCode: "fi", label: "Suomi"},
    {languageCode: "de", countryCode: "de", label: "Deutsch"},
    {languageCode: "nl", countryCode: "nl", label: "Nederlands"},
    {languageCode: "tr", countryCode: "tr", label: "Türk"},
    {languageCode: "sq", countryCode: "al", label: "Shqipe"},
    {languageCode: "pl", countryCode: "pl", label: "Polski"},
    {languageCode: "pt-BR", countryCode: "br", label: "Português brasileiro"},
    {languageCode: "el", countryCode: "gr", label: "Ελληνικά"},
    {languageCode: "ru", countryCode: "ru", label: "Русский"},
    {languageCode: "ar", countryCode: "ar", label: "العربية"},
    {languageCode: "ja", countryCode: "jp", label: "日本語"}
  ];

  constructor(appContext: AppContextService, public legacyRoutes: LegacyRoutesService,
              public usersService: UsersService) {
    this.appContext = appContext.get();
  }

  ngOnInit() {
  }
}
