from gql import gql

VISITOR_REVIEW_PHOTOS = gql("""
query getVisitorReviewPhotosInVisitorReviewTab($input: VisitorReviewPhotosInput) {
  visitorReviewPhotos(input: $input) {
    viewId
    originalUrl
    photoType
    mediaType
    logId
    relation
    title
    text
    date
    link
    sourceTitle
    externalLink {
      title
      url
    }
    author {
      id
      nickname
      from
      imageUrl
      objectId
      url
      borderImageUrl
    }
    votedKeywords {
      code
      iconUrl
      iconCode
      name
    }
    visitCount
    originType
    isFollowing
    rating
    video {
      videoId
      videoUrl
      trailerUrl
    }
  }
}
""")

FOLLOWING_REVIEWS = gql("""
query getFollowingReviews($input: FollowingReviewsInput) {
  followingReviews(input: $input) {
    reviews {
      id
      apolloCacheId
      rating
      author {
        id
        nickname
        from
        imageUrl
        objectId
        url
        review {
          totalCount
          imageCount
          avgRating
        }
        theme {
          totalCount
        }
        isFollowing
        followerCount
        followRequested
      }
      body
      thumbnail
      media {
        type
        thumbnail
        thumbnailRatio
        class
        videoId
        videoUrl
        trailerUrl
      }
      tags
      status
      visitCount
      viewCount
      visited
      created
      reply {
        editUrl
        body
        editedBy
        created
        date
        replyTitle
        isReported
        isSuspended
        status
      }
      originType
      item {
        name
        code
        options
      }
      businessName
      votedKeywords {
        code
        iconCode
        name
        iconUrl
      }
      visitCategories {
        code
        name
        keywords {
          code
          name
        }
      }
      userIdno
      loginIdno
      reactionStat {
        id
        typeCount {
          name
          count
        }
        totalCount
      }
      hasViewerReacted {
        id
        reacted
      }
      nickname
      representativeVisitDateTime
    }
    reactionTypes {
      name
      emojiUrl
      label
    }
  }
}
""")

VISITOR_RATING_REVIEWS = gql("""
query getVisitorRatingReviews($input: VisitorReviewsInput) {
  visitorReviews(input: $input) {
    total
    items {
      id
      cursor
      rating
      author {
        id
        nickname
        from
        imageUrl
        borderImageUrl
        objectId
        url
        review {
          totalCount
          imageCount
          avgRating
        }
        theme {
          totalCount
        }
        isFollowing
        followerCount
        followRequested
      }
      visitCount
      visited
      originType
      reply {
        editUrl
        body
        editedBy
        created
        date
        replyTitle
        isReported
        isSuspended
        status
      }
      votedKeywords {
        code
        iconUrl
        iconCode
        displayName
        name
      }
      businessName
      status
      userIdno
      loginIdno
      receiptInfoUrl
      reactionStat {
        id
        typeCount {
          name
          count
        }
        totalCount
      }
      hasViewerReacted {
        id
        reacted
      }
      nickname
    }
  }
}
""")

VISITOR_REVIEW_THEME_LISTS = gql("""
query getVisitorReviewThemeLists($input: ThemeListsInput) {
  themeLists(input: $input) {
    themeLists {
      id
      title
      viewCount
      itemCount
      reviews {
        businessName
        reviewBody
        imageUrl
      }
      authorNickname
      authorImageUrl
      isFollowing
      themeListUrl
      authorUrl
      cursor
    }
    total
  }
}
""")
