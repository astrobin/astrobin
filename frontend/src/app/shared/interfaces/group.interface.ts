export enum GroupCategory {
  PROFESSIONAL_NETWORK = "PROFESSIONAL_NETWORK",
  CLUB_OR_ASSOCIATION = "CLUB_OR_ASSOCIATION",
  INTERNET_COMMUNITY = "INTERNET_COMMUNITY",
  FRIENDS_OR_PARTNERS = "FRIENDS_OR_PARTNERS",
  GEOGRAPHICAL_AREA = "GEOGRAPHICAL_AREA",
  AD_HOC_COLLABORATION = "AD_HOC_COLLABORATION",
  SPECIFIC_TO_TECHNIQUE = "SPECIFIC_TO_TECHNIQUE",
  SPECIFIC_TO_TARGET = "SPECIFIC_TO_TARGET",
  SPECIFIC_TO_EQUIPMENT = "SPECIFIC_TO_EQUIPMENT",
  OTHER = "OTHER"
}

export interface GroupInterface {
  id: number;
  dateCreated: string;
  dateUpdated: string;
  creator: number;
  owner: number;
  name: string;
  description?: string;
  category: GroupCategory;
  public: boolean;
  moderated: boolean;
  autosubmission: boolean;
  moderators: number[];
  invitedUsers: number[];
  joinRequests: number[];
  images: number[];
  forum: number;
}
