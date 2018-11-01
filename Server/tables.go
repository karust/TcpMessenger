package main

import "github.com/jinzhu/gorm"

// Account ... Account table
type Account struct {
	//gorm.Model
	ID    uint
	Login string `gorm:"not null;unique"`
	Pass  string
}

type Group struct {
	//gorm.Model
	ID         uint
	Name       string `gorm:"not null;unique"`
	AdminID    uint   `gorm:"not null"`
	MembersNum uint32
}

type GroupMemebers struct {
	//gorm.Model
	ID  uint
	UID uint `gorm:"unique_index:UGID"`
	GID uint `gorm:"unique_index:UGID"`
}
type Messages struct {
	gorm.Model
}

type Message struct {
	gorm.Model
}
